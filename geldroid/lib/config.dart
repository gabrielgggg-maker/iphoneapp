import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static late SharedPreferences _p;

  static Future<void> init() async {
    _p = await SharedPreferences.getInstance();
  }

  static String get apiKey => _p.getString('api_key') ?? '';
  static set apiKey(String v) => _p.setString('api_key', v);

  static String get userId => _p.getString('user_id') ?? '';
  static set userId(String v) => _p.setString('user_id', v);

  static String get folderName => _p.getString('folder') ?? 'GelDroid';
  static set folderName(String v) => _p.setString('folder', v);

  static String get storageId => _p.getString('storage_id') ?? '';
  static set storageId(String v) => _p.setString('storage_id', v);

  static String get storageName => _p.getString('storage_name') ?? '';
  static set storageName(String v) => _p.setString('storage_name', v);

  static String get lastTags => _p.getString('last_tags') ?? '';
  static set lastTags(String v) => _p.setString('last_tags', v);

  static String get rating => _p.getString('rating') ?? '';
  static set rating(String v) => _p.setString('rating', v);

  // imagens decorativas escolhidas pelo usuario (slot -> caminho salvo no app)
  static String? customImage(String slot) => _p.getString('img_$slot');
  static Future<void> setCustomImage(String slot, String path) =>
      _p.setString('img_$slot', path);
  static Future<void> clearCustomImage(String slot) => _p.remove('img_$slot');

  // ids ja baixados (pra mostrar 'na galeria')
  static List<String> get downloaded => _p.getStringList('downloaded') ?? [];
  static bool isDownloaded(String id) => downloaded.contains(id);
  static Future<void> addDownloaded(String id) async {
    final l = downloaded;
    if (!l.contains(id)) {
      l.add(id);
      await _p.setStringList('downloaded', l);
    }
  }
}
