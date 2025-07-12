// lib/main.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:io' show Platform;

// The address of your local Flask API.
final String apiUrl = Platform.isAndroid
    ? 'http://10.0.2.2:5000/briefings'
    : 'http://127.0.0.1:5000/briefings';

// Data model for our Briefing object
class Briefing {
  final String summary;
  final DateTime startTime;
  final List<String> attendees;
  final List<String> documents;

  Briefing({
    required this.summary,
    required this.startTime,
    required this.attendees,
    required this.documents,
  });

  factory Briefing.fromJson(Map<String, dynamic> json) {
    return Briefing(
      summary: json['summary'],
      startTime: DateTime.parse(json['start_time']),
      // Ensure lists are correctly parsed from dynamic to String
      attendees: List<String>.from(json['attendees'] ?? []),
      documents: List<String>.from(json['documents'] ?? []),
    );
  }
}

Future<List<Briefing>> fetchBriefings() async {
  final response = await http.get(Uri.parse(apiUrl));

  if (response.statusCode == 200) {
    List jsonResponse = json.decode(response.body);
    return jsonResponse.map((data) => Briefing.fromJson(data)).toList();
  } else {
    throw Exception('Failed to load briefings from API');
  }
}

void main() {
  runApp(const MeetingMomentumApp());
}

class MeetingMomentumApp extends StatefulWidget {
  const MeetingMomentumApp({super.key});

  @override
  State<MeetingMomentumApp> createState() => _MeetingMomentumAppState();
}

class _MeetingMomentumAppState extends State<MeetingMomentumApp> {
  late Future<List<Briefing>> futureBriefings;

  @override
  void initState() {
    super.initState();
    futureBriefings = fetchBriefings();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Meeting Momentum',
      theme: ThemeData.dark(useMaterial3: true),
      home: Scaffold(
        appBar: AppBar(title: const Text('Meeting Momentum Briefings')),
        body: Center(
          child: FutureBuilder<List<Briefing>>(
            future: futureBriefings,
            builder: (context, snapshot) {
              if (snapshot.hasData) {
                return ListView.builder(
                  itemCount: snapshot.data!.length,
                  itemBuilder: (context, index) {
                    Briefing briefing = snapshot.data![index];
                    return Card(
                      margin: const EdgeInsets.all(10.0),
                      child: ListTile(
                        leading: const Icon(Icons.event_note, size: 40),
                        title: Text(
                          briefing.summary,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          'Attendees: ${briefing.attendees.length}\nDocuments: ${briefing.documents.length}',
                        ),
                        // UPDATED: Added onTap to handle navigation
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) =>
                                  BriefingDetailScreen(briefing: briefing),
                            ),
                          );
                        },
                      ),
                    );
                  },
                );
              } else if (snapshot.hasError) {
                return Text('${snapshot.error}');
              }
              return const CircularProgressIndicator();
            },
          ),
        ),
      ),
    );
  }
}

// NEW: A new screen widget to display the details of a single briefing.
class BriefingDetailScreen extends StatelessWidget {
  final Briefing briefing;

  const BriefingDetailScreen({super.key, required this.briefing});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(briefing.summary)),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            Text(
              'Time: ${briefing.startTime.toLocal()}', // Show in local time
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const Divider(height: 30),
            Text(
              'Attendees (${briefing.attendees.length})',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            // Display each attendee
            ...briefing.attendees.map((email) => Text('- $email')).toList(),
            const Divider(height: 30),
            Text(
              'Linked Documents (${briefing.documents.length})',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            // Display each document link
            ...briefing.documents
                .map(
                  (link) => Text(
                    link,
                    style: const TextStyle(color: Colors.lightBlueAccent),
                  ),
                )
                .toList(),
          ],
        ),
      ),
    );
  }
}
