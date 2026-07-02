import 'dart:io';
import 'package:gal/gal.dart';
import 'package:http/http.dart' as http;

class Volume {
  final String id;
  final String name;
  final bool removable;
  Volume(this.id, this.name, this.removable);
}

class Native {
  static Future<List<Volume>> volumes() async {
    final name = Platform.isIOS ? 'iPhone Storage' : 'Device Storage';
    return [Volume('internal', name, false)];
  }

  static Future<String?> saveToGallery({
    required String volumeId,
    required String folder,
    required String fileName,
    required String mime,
    required bool isVideo,
    required String tempPath,
  }) async {
    try {
      if (isVideo) {
        await Gal.putVideo(tempPath, album: folder);
      } else {
        await Gal.putImage(tempPath, album: folder);
      }
      return tempPath;
    } catch (_) {
      return null;
    }
  }
}

Future<File> downloadFile(
    String url, String destPath, void Function(double) onProgress) async {
  final client = http.Client();
  try {
    final req = http.Request('GET', Uri.parse(url));
    req.headers.addAll(const {
      'User-Agent': 'GelDroid/1.0',
      'Referer': 'https://gelbooru.com/',
    });
    final resp = await client.send(req);
    if (resp.statusCode != 200) {
      throw 'HTTP ${resp.statusCode}';
    }
    final total = resp.contentLength ?? 0;
    final file = File(destPath);
    await file.parent.create(recursive: true);
    final sink = file.openWrite();
    int received = 0;
    await for (final chunk in resp.stream) {
      sink.add(chunk);
      received += chunk.length;
      if (total > 0) onProgress(received / total);
    }
    await sink.close();
    onProgress(1.0);
    return file;
  } finally {
    client.close();
  }
}
