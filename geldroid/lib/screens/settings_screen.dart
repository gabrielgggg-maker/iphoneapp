import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../config.dart';
import '../theme.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _api = TextEditingController(text: AppConfig.apiKey);
  final _uid = TextEditingController(text: AppConfig.userId);
  final _folder = TextEditingController(text: AppConfig.folderName);

  void _save() {
    AppConfig.apiKey = _api.text.trim();
    AppConfig.userId = _uid.text.trim();
    AppConfig.folderName =
        _folder.text.trim().isEmpty ? 'GelDroid' : _folder.text.trim();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Saved! This kitty is ready to serve you, nya~ 😈'),
          backgroundColor: kPurple),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: kBg,
        title: Text('Settings', style: TextStyle(shadows: neonShadow(kPink))),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section('Gelbooru API access'),
          const Text(
            'Get it from Gelbooru -> your account -> Options -> API Access '
            'Credentials. Paste both fields below (without them the search may '
            'be refused).',
            style: TextStyle(color: kDim, fontSize: 12),
          ),
          const SizedBox(height: 10),
          _field('API key', _api),
          _field('User ID', _uid),
          const SizedBox(height: 20),
          _section('Where to save'),
          _field('Album name (created automatically)', _folder),
          const SizedBox(height: 20),
          _section('Permissions'),
          OutlinedButton.icon(
            onPressed: () async {
              await [Permission.photos, Permission.storage].request();
            },
            icon: const Icon(Icons.lock_open, color: kPink),
            label: const Text('Grant gallery access',
                style: TextStyle(color: kPink)),
          ),
          const SizedBox(height: 30),
          GestureDetector(
            onTap: _save,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: glowBox(radius: 16),
              child: const Center(
                child: Text('SAVE',
                    style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 1.5)),
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _section(String t) => Padding(
        padding: const EdgeInsets.only(bottom: 8, top: 4),
        child: Text(t,
            style: TextStyle(
                color: kPink2,
                fontSize: 15,
                fontWeight: FontWeight.bold,
                shadows: neonShadow(kPink))),
      );

  Widget _field(String label, TextEditingController c) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
          controller: c,
          style: const TextStyle(color: kText),
          decoration: InputDecoration(labelText: label,
              labelStyle: const TextStyle(color: kDim)),
        ),
      );
}
