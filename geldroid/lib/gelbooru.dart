import 'dart:convert';
import 'package:http/http.dart' as http;
import 'config.dart';

int _toInt(dynamic v) {
  if (v is int) return v;
  if (v is String) return int.tryParse(v) ?? 0;
  return 0;
}

class Post {
  final String id, fileUrl, previewUrl, sampleUrl, source, rating, tags;
  final int width, height;

  Post({
    required this.id,
    required this.fileUrl,
    required this.previewUrl,
    required this.sampleUrl,
    required this.source,
    required this.rating,
    required this.tags,
    required this.width,
    required this.height,
  });

  factory Post.fromJson(Map<String, dynamic> j) => Post(
        id: '${j['id'] ?? ''}',
        fileUrl: (j['file_url'] ?? '') as String,
        previewUrl: (j['preview_url'] ?? '') as String,
        sampleUrl: (j['sample_url'] ?? '') as String,
        source: (j['source'] ?? '') as String,
        rating: (j['rating'] ?? '') as String,
        tags: (j['tags'] ?? '') as String,
        width: _toInt(j['width']),
        height: _toInt(j['height']),
      );

  String get ext {
    final u = fileUrl.split('?').first.toLowerCase();
    final dot = u.lastIndexOf('.');
    if (dot != -1 && u.length - dot <= 5) return u.substring(dot);
    return '.jpg';
  }

  bool get isVideo =>
      const ['.mp4', '.webm', '.mkv', '.mov'].contains(ext);
  bool get isGif => ext == '.gif';

  String get mime {
    switch (ext) {
      case '.png':
        return 'image/png';
      case '.gif':
        return 'image/gif';
      case '.webp':
        return 'image/webp';
      case '.mp4':
        return 'video/mp4';
      case '.webm':
        return 'video/webm';
      case '.mkv':
        return 'video/x-matroska';
      case '.mov':
        return 'video/quicktime';
      default:
        return 'image/jpeg';
    }
  }

  String get fileName => 'gelbooru_$id$ext';
  String get thumb =>
      previewUrl.isNotEmpty ? previewUrl : (sampleUrl.isNotEmpty ? sampleUrl : fileUrl);

  String get postUrl =>
      'https://gelbooru.com/index.php?page=post&s=view&id=$id';
}

class Gelbooru {
  static const base = 'https://gelbooru.com/index.php';
  static const headers = {
    'User-Agent': 'GelDroid/1.0',
    'Referer': 'https://gelbooru.com/',
  };

  static Future<List<Post>> search(String tags,
      {int limit = 40, int pid = 0}) async {
    final params = <String, String>{
      'page': 'dapi',
      's': 'post',
      'q': 'index',
      'json': '1',
      'tags': tags.trim(),
      'limit': '$limit',
      'pid': '$pid',
    };
    if (AppConfig.apiKey.isNotEmpty && AppConfig.userId.isNotEmpty) {
      params['api_key'] = AppConfig.apiKey;
      params['user_id'] = AppConfig.userId;
    }
    final uri = Uri.parse(base).replace(queryParameters: params);
    final r = await http.get(uri, headers: headers);
    if (r.statusCode != 200) {
      throw 'HTTP ${r.statusCode} (check api_key / user_id in Settings)';
    }
    final body = r.body.trim();
    if (body.isEmpty) return [];
    final data = jsonDecode(body);
    List raw;
    if (data is List) {
      raw = data;
    } else if (data is Map && data['post'] != null) {
      raw = data['post'] is List ? data['post'] : [data['post']];
    } else {
      raw = [];
    }
    return raw
        .whereType<Map>()
        .map((e) => Post.fromJson(e.cast<String, dynamic>()))
        .where((p) => p.fileUrl.isNotEmpty)
        .toList();
  }
}
