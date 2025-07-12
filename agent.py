# agent.py
import logging
import asyncio
import asyncpg
from functools import partial

from sentient_agent_framework import (
    AbstractAgent,
    DefaultServer,
    Session,
    Query,
    ResponseHandler
)

# Import our existing Google client logic
from google_client import get_briefings 

# --- Database Configuration ---
DB_PARAMS = {
    "database": "meeting_momentum",
    "user": "postgres", # Or your username
    "password": "143256", # Your actual password
    "host": "localhost"
}

# --- Agent Definition ---
class MeetingMomentumAgent(AbstractAgent):
    """An agent to help users prepare for their meetings."""

    # Implement the required `assist` method
    async def assist(self, session: Session, query: Query, response_handler: ResponseHandler):
        """
        Handles requests from the Sentient Chat UI.
        The 'query.prompt' will contain the user's command.
        """
        command = query.prompt.lower().strip()

        if command == "sync":
            await self.handle_sync(response_handler)
        elif command == "show briefings":
            await self.handle_show_briefings(response_handler)
        else:
            await response_handler.emit_text_block("ERROR", f"Unknown command: '{command}'. Try 'sync' or 'show briefings'.")

        # Signal that the response is complete
        await response_handler.complete()

    async def handle_sync(self, response_handler: ResponseHandler):
        """Handles the 'sync' command."""
        await response_handler.emit_text_block("STATUS", "Connecting to Google Calendar...")
        await response_handler.emit_text_block("STATUS", "If this is your first time, a browser may open for you to sign in...")

        
        # The Google client library is not async, so we run it in a thread
        loop = asyncio.get_running_loop()
        briefings = await loop.run_in_executor(None, get_briefings)

        if not briefings:
            await response_handler.emit_text_block("RESULT", "No upcoming events found.")
            return

        await response_handler.emit_text_block("STATUS", "Saving briefings to the database...")
        conn = await asyncpg.connect(**DB_PARAMS)
        
        # This is an async database query
        upsert_query = """
            INSERT INTO briefings (event_id, event_summary, start_time, attendees, documents, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            ON CONFLICT (event_id) DO UPDATE SET
                event_summary = EXCLUDED.event_summary, start_time = EXCLUDED.start_time,
                attendees = EXCLUDED.attendees, documents = EXCLUDED.documents, updated_at = NOW();
        """
        
        # Prepare and execute the query for all briefings
        await conn.executemany(upsert_query, [
            (b['event_id'], b['summary'], b['start_time'], b['attendees'], b['documents']) for b in briefings
        ])
        await conn.close()

        await response_handler.emit_text_block("RESULT", f"Sync complete. Found and saved {len(briefings)} events.")

    async def handle_show_briefings(self, response_handler: ResponseHandler):
        """Handles the 'show briefings' command."""
        await response_handler.emit_text_block("STATUS", "Fetching briefings from the database...")
        conn = await asyncpg.connect(**DB_PARAMS)

        rows = await conn.fetch("SELECT event_summary, start_time, attendees, documents FROM briefings ORDER BY start_time ASC")
        await conn.close()

        if not rows:
            await response_handler.emit_text_block("RESULT", "No briefings found. Try running 'sync' first.")
            return

        # Format the data for the client
        briefings_json = [{
            "summary": row['event_summary'],
            "start_time": row['start_time'].isoformat(),
            "attendees": row['attendees'],
            "documents": row['documents']
        } for row in rows]

        # Use emit_json to send the structured data to the Sentient Chat UI
        await response_handler.emit_json("BRIEFINGS", {"results": briefings_json})


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create an instance of our agent
    agent = MeetingMomentumAgent(name="Meeting Momentum")
    
    # Create a server as required by the framework
    server = DefaultServer(agent)
    
    # Run the server
    print("🚀 Meeting Momentum Agent is running. Ready to receive commands.")
    server.run()