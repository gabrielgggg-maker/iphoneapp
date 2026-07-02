#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║                       GelDroid                           ║
║      Gelbooru -> Galeria do celular (imagens/gif/video)  ║
║                 Script de Build v1.0                     ║
╚══════════════════════════════════════════════════════════╝

Uso:  python build_app.py [--debug] [--clean]

Faz tudo sozinho: acha/clona o Flutter, detecta Android SDK + Java,
aceita licencas, gera o projeto Flutter (todo o codigo Dart fica embutido
aqui dentro), cria o icone e compila o APK final em GelDroid.apk.

App GelDroid:
  - Busca no Gelbooru por tags (voce coloca api_key + user_id na tela Config).
  - Baixa imagem / GIF / video direto pra galeria.
  - Animacao moderna em volta da imagem mostrando o progresso do download.
  - Marca o que ja foi baixado / ja esta na galeria.
  - Escolhe salvar no armazenamento interno OU no cartao de memoria.
  - Escolhe o nome da pasta (ele cria sozinho e salva la).
  - Tema lewd/ecchi com banner e tela de loading animada.
  - Menu unico pra escolher (da sua galeria) as imagens do banner e do loading,
    que ficam salvas dentro do app mesmo depois de fechar.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

# ─────────────── Configuracoes ───────────────
IS_WINDOWS = platform.system() == "Windows"
IS_MAC     = platform.system() == "Darwin"
IS_DEBUG   = "--debug" in sys.argv
IS_CLEAN   = "--clean" in sys.argv

PROJECT_NAME = "geldroid"
ORG          = "com.geldroid"
APP_ID       = "com.geldroid.geldroid"
APP_LABEL    = "GelDroid"

SCRIPT_DIR  = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR / PROJECT_NAME
ASSETS_DIR  = PROJECT_DIR / "assets" / "images"
FLUTTER_DIR = Path.home() / "flutter_git"

# ─────────────── Cores ───────────────
VERMELHO = "\033[91m"; VERDE = "\033[92m"; AMARELO = "\033[93m"
AZUL = "\033[94m"; CIANO = "\033[96m"; RESET = "\033[0m"; NEGRITO = "\033[1m"

def titulo(msg): print(f"\n{AZUL}{NEGRITO}{'='*60}{RESET}\n{AZUL}{NEGRITO}  {msg}{RESET}\n{AZUL}{NEGRITO}{'='*60}{RESET}\n")
def ok(msg):    print(f"  {VERDE}OK{RESET} {msg}")
def erro(msg):  print(f"  {VERMELHO}ERRO: {msg}{RESET}")
def info(msg):  print(f"  {CIANO}->{RESET} {msg}")
def aviso(msg): print(f"  {AMARELO}!{RESET} {msg}")


# ═══════════════════════════════════════════════════════
#  ARQUIVOS DE CONFIG DO PROJETO
# ═══════════════════════════════════════════════════════

PUBSPEC_YAML = """\
name: geldroid
description: GelDroid - baixe imagens, gifs e videos do Gelbooru direto pra galeria.
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  shared_preferences: ^2.3.2
  permission_handler: ^11.3.1
  path_provider: ^2.1.4
  image_picker: ^1.1.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_launcher_icons: ^0.13.1
  flutter_lints: ^4.0.0

flutter_launcher_icons:
  android: true
  ios: false
  image_path: "assets/images/icon.png"
  min_sdk_android: 21

flutter:
  uses-material-design: true
  assets:
    - assets/images/
"""

ANDROID_MANIFEST = """\
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE"/>
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO"/>
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32"/>
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28"/>

    <application
        android:label="GelDroid"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:requestLegacyExternalStorage="true"
        android:usesCleartextTraffic="true">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">

            <meta-data
                android:name="io.flutter.embedding.android.NormalTheme"
                android:resource="@style/NormalTheme"/>

            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>

        <meta-data
            android:name="flutterEmbedding"
            android:value="2"/>
    </application>
</manifest>
"""

SETTINGS_GRADLE_KTS = """\
pluginManagement {
    val flutterSdkPath =
        run {
            val properties = java.util.Properties()
            file("local.properties").inputStream().use { properties.load(it) }
            val flutterSdkPath = properties.getProperty("flutter.sdk")
            require(flutterSdkPath != null) { "flutter.sdk not set in local.properties" }
            flutterSdkPath
        }

    includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

plugins {
    id("dev.flutter.flutter-plugin-loader") version "1.0.0"
    id("com.android.application") version "9.0.1" apply false
    id("org.jetbrains.kotlin.android") version "2.3.20" apply false
}

include(":app")
"""

ROOT_BUILD_GRADLE_KTS = """\
allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
"""

APP_BUILD_GRADLE_KTS = """\
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.geldroid.geldroid"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        isCoreLibraryDesugaringEnabled = true
    }

    defaultConfig {
        applicationId = "com.geldroid.geldroid"
        minSdk = maxOf(flutter.minSdkVersion, 21)
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}

flutter {
    source = "../.."
}
"""

GRADLE_PROPERTIES = """\
org.gradle.jvmargs=-Xmx8G -XX:MaxMetaspaceSize=4G -XX:ReservedCodeCacheSize=512m -XX:+HeapDumpOnOutOfMemoryError
android.useAndroidX=true
android.newDsl=false
android.builtInKotlin=false
"""

MAIN_ACTIVITY_KT = """\
package com.geldroid.geldroid

import android.content.ContentValues
import android.media.MediaScannerConnection
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.File

class MainActivity : FlutterActivity() {
    private val channelName = "geldroid/native"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName)
            .setMethodCallHandler { call, result ->
                try {
                    when (call.method) {
                        "listVolumes" -> result.success(listVolumes())
                        "saveToGallery" -> result.success(
                            saveToGallery(
                                call.argument<String>("volumeId") ?: "external_primary",
                                call.argument<String>("folder") ?: "GelDroid",
                                call.argument<String>("fileName") ?: "file",
                                call.argument<String>("mime") ?: "image/jpeg",
                                call.argument<Boolean>("isVideo") ?: false,
                                call.argument<String>("tempPath") ?: ""
                            )
                        )
                        else -> result.notImplemented()
                    }
                } catch (e: Exception) {
                    result.error("ERR", e.message, null)
                }
            }
    }

    // Lista os volumes reais do MediaStore: interno + cartao(oes) de memoria.
    private fun listVolumes(): List<Map<String, Any>> {
        val out = ArrayList<Map<String, Any>>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            for (n in MediaStore.getExternalVolumeNames(applicationContext)) {
                val primary = n == MediaStore.VOLUME_EXTERNAL_PRIMARY
                out.add(
                    mapOf(
                        "id" to n,
                        "name" to if (primary) "Internal storage" else "Memory card ($n)",
                        "removable" to !primary
                    )
                )
            }
        } else {
            out.add(
                mapOf(
                    "id" to "external_primary",
                    "name" to "Internal storage",
                    "removable" to false
                )
            )
        }
        return out
    }

    // Salva no volume escolhido (interno OU cartao) via MediaStore, criando a
    // pasta e fazendo a midia aparecer na galeria automaticamente.
    private fun saveToGallery(
        volumeId: String, folder: String, fileName: String,
        mime: String, isVideo: Boolean, tempPath: String
    ): String {
        val resolver = applicationContext.contentResolver
        val src = File(tempPath)
        if (!src.exists()) throw Exception("temporary file does not exist")

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val collection =
                if (isVideo) MediaStore.Video.Media.getContentUri(volumeId)
                else MediaStore.Images.Media.getContentUri(volumeId)
            val relBase =
                if (isVideo) Environment.DIRECTORY_MOVIES else Environment.DIRECTORY_PICTURES
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, mime)
                put(MediaStore.MediaColumns.RELATIVE_PATH, "$relBase/$folder")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
            val uri = resolver.insert(collection, values)
                ?: throw Exception("could not write to the selected storage")
            (resolver.openOutputStream(uri)
                ?: throw Exception("failed to open output")).use { out ->
                src.inputStream().use { it.copyTo(out) }
            }
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
            src.delete()
            return uri.toString()
        } else {
            val baseDir = Environment.getExternalStoragePublicDirectory(
                if (isVideo) Environment.DIRECTORY_MOVIES else Environment.DIRECTORY_PICTURES
            )
            val dir = File(baseDir, folder)
            dir.mkdirs()
            val dest = File(dir, fileName)
            src.copyTo(dest, overwrite = true)
            src.delete()
            MediaScannerConnection.scanFile(
                applicationContext, arrayOf(dest.absolutePath), arrayOf(mime), null
            )
            return dest.absolutePath
        }
    }
}
"""

# ═══════════════════════════════════════════════════════
#  CODIGO DART (lib/)
# ═══════════════════════════════════════════════════════

DART_MAIN = """\
import 'package:flutter/material.dart';
import 'config.dart';
import 'theme.dart';
import 'screens/splash_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppConfig.init();
  runApp(const GelDroidApp());
}

class GelDroidApp extends StatelessWidget {
  const GelDroidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GelDroid',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: const SplashScreen(),
    );
  }
}
"""

DART_THEME = """\
import 'package:flutter/material.dart';

const kPink = Color(0xFFFF4F8B);
const kPink2 = Color(0xFFFF8FB8);
const kPurple = Color(0xFFA64BFF);
const kBg = Color(0xFF120612);
const kPanel = Color(0xFF1E0F22);
const kPanel2 = Color(0xFF2A1530);
const kText = Color(0xFFF3E6F0);
const kDim = Color(0xFFB89AB0);

ThemeData buildTheme() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: kBg,
    primaryColor: kPink,
    useMaterial3: true,
    colorScheme: const ColorScheme.dark(
      primary: kPink,
      secondary: kPurple,
      surface: kPanel,
      onPrimary: Colors.white,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: kPanel2,
      hintStyle: const TextStyle(color: kDim),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide.none,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    ),
  );
}

const kGlowGradient = LinearGradient(
  colors: [kPink, kPurple],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

List<Shadow> neonShadow(Color c) => [
      Shadow(color: c.withOpacity(0.9), blurRadius: 12),
      Shadow(color: c.withOpacity(0.6), blurRadius: 26),
    ];

BoxDecoration glowBox({double radius = 18, Color color = kPink}) => BoxDecoration(
      borderRadius: BorderRadius.circular(radius),
      gradient: kGlowGradient,
      boxShadow: [
        BoxShadow(color: color.withOpacity(0.45), blurRadius: 18, spreadRadius: 1),
      ],
    );
"""

DART_CONFIG = """\
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
"""

DART_GELBOORU = """\
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
"""

DART_STORAGE = """\
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

class Volume {
  final String id;
  final String name;
  final bool removable;
  Volume(this.id, this.name, this.removable);
}

class Native {
  static const _ch = MethodChannel('geldroid/native');

  static Future<List<Volume>> volumes() async {
    try {
      final res = await _ch.invokeMethod('listVolumes');
      return (res as List)
          .map((m) => Volume(
                (m['id'] ?? '') as String,
                (m['name'] ?? 'Storage') as String,
                (m['removable'] ?? false) as bool,
              ))
          .where((v) => v.id.isNotEmpty)
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Move o arquivo temporario pro volume escolhido (interno ou cartao) via
  /// MediaStore. Retorna a uri salva, ou null se falhar.
  static Future<String?> saveToGallery({
    required String volumeId,
    required String folder,
    required String fileName,
    required String mime,
    required bool isVideo,
    required String tempPath,
  }) async {
    final r = await _ch.invokeMethod('saveToGallery', {
      'volumeId': volumeId,
      'folder': folder,
      'fileName': fileName,
      'mime': mime,
      'isVideo': isVideo,
      'tempPath': tempPath,
    });
    return r as String?;
  }
}

/// Baixa qualquer arquivo (imagem/gif/video) com progresso (0..1).
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
"""

DART_SPLASH = """\
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../config.dart';
import '../phrases.dart';
import '../storage.dart';
import '../theme.dart';
import 'root_nav.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  final String _line = randomLewd();

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..forward();
    _boot();
  }

  Future<void> _boot() async {
    await _perms();
    await _defaultStorage();
    await Future.delayed(const Duration(milliseconds: 1600));
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const RootNav()),
    );
  }

  Future<void> _perms() async {
    await [Permission.photos, Permission.videos, Permission.storage].request();
  }

  Future<void> _defaultStorage() async {
    if (AppConfig.storageId.isEmpty) {
      final v = await Native.volumes();
      if (v.isNotEmpty) {
        final internal =
            v.firstWhere((e) => !e.removable, orElse: () => v.first);
        AppConfig.storageId = internal.id;
        AppConfig.storageName = internal.name;
      }
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final custom = AppConfig.customImage('splash');
    final fade = CurvedAnimation(parent: _c, curve: Curves.easeOut);
    final scale = Tween(begin: 0.82, end: 1.0)
        .animate(CurvedAnimation(parent: _c, curve: Curves.easeOutBack));

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            colors: [kPanel2, kBg],
            radius: 1.1,
          ),
        ),
        child: Center(
          child: FadeTransition(
            opacity: fade,
            child: ScaleTransition(
              scale: scale,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _logo(custom),
                  const SizedBox(height: 26),
                  Text(
                    'GelDroid',
                    style: TextStyle(
                      fontSize: 40,
                      fontWeight: FontWeight.w900,
                      color: kPink2,
                      letterSpacing: 1.5,
                      shadows: neonShadow(kPink),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 40),
                    child: Text(_line,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            color: kPink2,
                            fontStyle: FontStyle.italic,
                            fontSize: 13)),
                  ),
                  const SizedBox(height: 30),
                  const SizedBox(
                    width: 150,
                    child: LinearProgressIndicator(
                      color: kPink,
                      backgroundColor: kPanel2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _logo(String? custom) {
    if (custom != null && File(custom).existsSync()) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(28),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(28),
            boxShadow: [BoxShadow(color: kPink.withOpacity(0.5), blurRadius: 30)],
          ),
          child: Image.file(File(custom),
              width: 180, height: 180, fit: BoxFit.cover),
        ),
      );
    }
    return Container(
      width: 150,
      height: 150,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: kGlowGradient,
        boxShadow: [BoxShadow(color: kPink.withOpacity(0.6), blurRadius: 36)],
      ),
      child: const Icon(Icons.favorite, size: 78, color: Colors.white),
    );
  }
}
"""

DART_ROOTNAV = """\
import 'package:flutter/material.dart';
import '../theme.dart';
import 'home_screen.dart';
import 'customize_screen.dart';
import 'settings_screen.dart';

class RootNav extends StatefulWidget {
  const RootNav({super.key});
  @override
  State<RootNav> createState() => _RootNavState();
}

class _RootNavState extends State<RootNav> {
  int _i = 0;
  final _pages = const [HomeScreen(), CustomizeScreen(), SettingsScreen()];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_i],
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          backgroundColor: kPanel,
          indicatorColor: kPink.withOpacity(0.25),
          labelTextStyle: WidgetStateProperty.all(
            const TextStyle(color: kDim, fontSize: 12),
          ),
        ),
        child: NavigationBar(
          selectedIndex: _i,
          onDestinationSelected: (v) => setState(() => _i = v),
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.search, color: kDim),
                selectedIcon: Icon(Icons.search, color: kPink),
                label: 'Search'),
            NavigationDestination(
                icon: Icon(Icons.palette_outlined, color: kDim),
                selectedIcon: Icon(Icons.palette, color: kPink),
                label: 'Customize'),
            NavigationDestination(
                icon: Icon(Icons.settings_outlined, color: kDim),
                selectedIcon: Icon(Icons.settings, color: kPink),
                label: 'Settings'),
          ],
        ),
      ),
    );
  }
}
"""

DART_HOME = """\
import 'dart:io';
import 'package:flutter/material.dart';
import '../config.dart';
import '../gelbooru.dart';
import '../phrases.dart';
import '../theme.dart';
import '../widgets/image_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _tagCtrl = TextEditingController(text: AppConfig.lastTags);
  final _scroll = ScrollController();
  final List<Post> _posts = [];
  final String _bannerLine = randomLewd();
  final String _emptyLine = randomLewd();
  String _tags = '';
  int _pid = 0;
  bool _loading = false;
  bool _end = false;
  String? _error;
  String _rating = AppConfig.rating;

  @override
  void initState() {
    super.initState();
    _scroll.addListener(() {
      if (_scroll.position.pixels >=
          _scroll.position.maxScrollExtent - 400) {
        _loadMore();
      }
    });
  }

  String _ratingTag() {
    switch (_rating) {
      case 'general':
        return 'rating:general';
      case 'sensitive':
        return 'rating:sensitive';
      case 'questionable':
        return 'rating:questionable';
      case 'explicit':
        return 'rating:explicit';
      default:
        return '';
    }
  }

  String _fullTags() {
    final parts = [_tagCtrl.text.trim(), _ratingTag()];
    return parts.where((p) => p.isNotEmpty).join(' ').trim();
  }

  Future<void> _search() async {
    AppConfig.lastTags = _tagCtrl.text.trim();
    AppConfig.rating = _rating;
    setState(() {
      _posts.clear();
      _pid = 0;
      _end = false;
      _error = null;
      _tags = _fullTags();
    });
    await _fetch();
  }

  Future<void> _loadMore() async {
    if (_loading || _end || _posts.isEmpty) return;
    _pid++;
    await _fetch();
  }

  Future<void> _fetch() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final r = await Gelbooru.search(_tags, limit: 40, pid: _pid);
      setState(() {
        if (r.isEmpty) _end = true;
        _posts.addAll(r);
      });
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bg = AppConfig.customImage('background');
    final hasBg = bg != null && File(bg).existsSync();
    return Scaffold(
      body: Stack(
        children: [
          if (hasBg)
            Positioned.fill(
              child: Opacity(
                opacity: 0.16,
                child: Image.file(File(bg), fit: BoxFit.cover),
              ),
            ),
          SafeArea(
            bottom: false,
            child: Column(
              children: [
                _Banner(subtitle: _bannerLine),
                _searchBar(),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(_error!, style: const TextStyle(color: kPink)),
                  ),
                Expanded(child: _grid()),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _searchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 6),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _tagCtrl,
                  style: const TextStyle(color: kText),
                  decoration: const InputDecoration(
                    hintText: 'tags (e.g. hatsune_miku feet)',
                    prefixIcon: Icon(Icons.tag, color: kDim),
                  ),
                  onSubmitted: (_) => _search(),
                ),
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _search,
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: glowBox(radius: 14),
                  child: const Icon(Icons.search, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          SizedBox(
            height: 36,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _chip('All', ''),
                _chip('General', 'general'),
                _chip('Sensitive', 'sensitive'),
                _chip('Questionable', 'questionable'),
                _chip('Explicit', 'explicit'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _chip(String label, String val) {
    final sel = _rating == val;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: sel,
        showCheckmark: false,
        labelStyle: TextStyle(color: sel ? Colors.white : kDim),
        backgroundColor: kPanel2,
        selectedColor: kPurple,
        onSelected: (_) => setState(() => _rating = val),
      ),
    );
  }

  Widget _grid() {
    if (_posts.isEmpty && _loading) {
      return const Center(child: CircularProgressIndicator(color: kPink));
    }
    if (_posts.isEmpty) {
      final empty = AppConfig.customImage('empty');
      final hasEmpty = empty != null && File(empty).existsSync();
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (hasEmpty)
              ClipRRect(
                borderRadius: BorderRadius.circular(20),
                child: Image.file(File(empty),
                    width: 180, height: 180, fit: BoxFit.cover),
              )
            else
              Icon(Icons.favorite_border, color: kPink.withOpacity(0.5), size: 70),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: Text(_emptyLine,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                      color: kPink2, fontStyle: FontStyle.italic, fontSize: 14)),
            ),
          ],
        ),
      );
    }
    return GridView.builder(
      controller: _scroll,
      padding: const EdgeInsets.all(10),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 0.72,
      ),
      itemCount: _posts.length + (_loading ? 1 : 0),
      itemBuilder: (ctx, i) {
        if (i >= _posts.length) {
          return const Center(child: CircularProgressIndicator(color: kPink));
        }
        return ImageCard(_posts[i]);
      },
    );
  }
}

class _Banner extends StatelessWidget {
  final String subtitle;
  const _Banner({required this.subtitle});

  @override
  Widget build(BuildContext context) {
    final custom = AppConfig.customImage('banner');
    return Container(
      height: 116,
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: kGlowGradient,
        boxShadow: [BoxShadow(color: kPink.withOpacity(0.4), blurRadius: 18)],
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (custom != null && File(custom).existsSync())
            Image.file(File(custom), fit: BoxFit.cover),
          if (custom != null && File(custom).existsSync())
            Container(color: Colors.black.withOpacity(0.35)),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('GelDroid',
                    style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        shadows: neonShadow(kPurple))),
                const SizedBox(height: 4),
                Text(subtitle,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                        color: Colors.white,
                        fontStyle: FontStyle.italic,
                        fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
"""

DART_IMAGECARD = """\
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import '../config.dart';
import '../gelbooru.dart';
import '../phrases.dart';
import '../storage.dart';
import '../theme.dart';

class ImageCard extends StatefulWidget {
  final Post post;
  const ImageCard(this.post, {super.key});
  @override
  State<ImageCard> createState() => _ImageCardState();
}

class _ImageCardState extends State<ImageCard> {
  double _progress = 0;
  bool _downloading = false;
  bool _done = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _done = AppConfig.isDownloaded(widget.post.id);
  }

  Future<void> _download() async {
    if (_downloading || _done) return;
    final volumeId = AppConfig.storageId;
    if (volumeId.isEmpty) {
      setState(() => _error = 'Pick a storage in Settings');
      return;
    }
    final folder = AppConfig.folderName.trim().isEmpty
        ? 'GelDroid'
        : AppConfig.folderName.trim();
    setState(() {
      _downloading = true;
      _progress = 0;
      _error = null;
    });
    try {
      final tmpDir = await getTemporaryDirectory();
      final tmp = '${tmpDir.path}/${widget.post.fileName}';
      await downloadFile(widget.post.fileUrl, tmp, (p) {
        if (mounted) setState(() => _progress = p);
      });
      final uri = await Native.saveToGallery(
        volumeId: volumeId,
        folder: folder,
        fileName: widget.post.fileName,
        mime: widget.post.mime,
        isVideo: widget.post.isVideo,
        tempPath: tmp,
      );
      if (uri == null) throw 'failed to save to storage';
      await AppConfig.addDownloaded(widget.post.id);
      if (mounted) {
        setState(() {
          _downloading = false;
          _done = true;
          _progress = 1;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(randomLewd()),
            backgroundColor: kPurple,
            duration: const Duration(milliseconds: 1600),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _downloading = false;
          _error = '$e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final post = widget.post;
    return GestureDetector(
      onTap: _download,
      child: Stack(
        fit: StackFit.expand,
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: Image.network(
              post.thumb,
              fit: BoxFit.cover,
              headers: Gelbooru.headers,
              loadingBuilder: (c, w, prog) => prog == null
                  ? w
                  : Container(
                      color: kPanel2,
                      child: const Center(
                          child: CircularProgressIndicator(
                              color: kPink, strokeWidth: 2))),
              errorBuilder: (c, e, s) => Container(
                  color: kPanel2,
                  child: const Icon(Icons.broken_image, color: kDim)),
            ),
          ),
          // moldura animada de progresso
          if (_downloading)
            Positioned.fill(
              child: CustomPaint(
                painter: _BorderProgressPainter(_progress),
              ),
            ),
          if (_downloading)
            Positioned.fill(
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Center(
                  child: Text(
                    '${(_progress * 100).toStringAsFixed(0)}%',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      shadows: neonShadow(kPink),
                    ),
                  ),
                ),
              ),
            ),
          // badges de tipo
          Positioned(
            left: 8,
            top: 8,
            child: Row(
              children: [
                if (post.isVideo) _badge('VIDEO', Icons.play_arrow),
                if (post.isGif) _badge('GIF', Icons.gif_box),
              ],
            ),
          ),
          // status / botao
          Positioned(
            right: 8,
            bottom: 8,
            child: _statusWidget(),
          ),
          if (_error != null)
            Positioned(
              left: 6,
              right: 6,
              bottom: 6,
              child: Container(
                padding: const EdgeInsets.all(4),
                color: Colors.black54,
                child: Text(_error!,
                    style: const TextStyle(color: kPink, fontSize: 10),
                    maxLines: 2, overflow: TextOverflow.ellipsis),
              ),
            ),
        ],
      ),
    );
  }

  Widget _statusWidget() {
    if (_done) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.green.shade600,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [BoxShadow(color: Colors.green.withOpacity(0.5), blurRadius: 8)],
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.check, color: Colors.white, size: 16),
            SizedBox(width: 4),
            Text('In gallery',
                style: TextStyle(color: Colors.white, fontSize: 11)),
          ],
        ),
      );
    }
    if (_downloading) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: glowBox(radius: 30),
      child: const Icon(Icons.download_rounded, color: Colors.white, size: 20),
    );
  }

  Widget _badge(String text, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: kPink2, size: 13),
          const SizedBox(width: 3),
          Text(text, style: const TextStyle(color: Colors.white, fontSize: 10)),
        ],
      ),
    );
  }
}

class _BorderProgressPainter extends CustomPainter {
  final double progress;
  _BorderProgressPainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final rrect = RRect.fromRectAndRadius(
        Offset.zero & size, const Radius.circular(16));
    final bg = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4
      ..color = Colors.white24;
    canvas.drawRRect(rrect, bg);

    final path = Path()..addRRect(rrect);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round
      ..shader = const LinearGradient(colors: [kPink, kPurple])
          .createShader(Offset.zero & size)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2);

    for (final m in path.computeMetrics()) {
      canvas.drawPath(m.extractPath(0, m.length * progress.clamp(0.0, 1.0)), paint);
    }
  }

  @override
  bool shouldRepaint(_BorderProgressPainter old) => old.progress != progress;
}
"""

DART_SETTINGS = """\
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../config.dart';
import '../storage.dart';
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
  List<Volume> _vols = [];
  String _selId = AppConfig.storageId;

  @override
  void initState() {
    super.initState();
    _loadVols();
  }

  Future<void> _loadVols() async {
    final v = await Native.volumes();
    setState(() {
      _vols = v;
      if (_selId.isEmpty && v.isNotEmpty) {
        _selId = v.firstWhere((e) => !e.removable, orElse: () => v.first).id;
      }
    });
  }

  void _save() {
    AppConfig.apiKey = _api.text.trim();
    AppConfig.userId = _uid.text.trim();
    AppConfig.folderName =
        _folder.text.trim().isEmpty ? 'GelDroid' : _folder.text.trim();
    if (_selId.isNotEmpty) {
      AppConfig.storageId = _selId;
      final v = _vols.where((e) => e.id == _selId);
      if (v.isNotEmpty) AppConfig.storageName = v.first.name;
    }
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
          _field('Folder name (created automatically)', _folder),
          const SizedBox(height: 10),
          const Text('Storage:', style: TextStyle(color: kDim)),
          ..._vols.map(_volTile),
          if (_vols.isEmpty)
            TextButton.icon(
              onPressed: _loadVols,
              icon: const Icon(Icons.refresh, color: kPink),
              label: const Text('Reload storage',
                  style: TextStyle(color: kPink)),
            ),
          const SizedBox(height: 20),
          _section('Permissions'),
          OutlinedButton.icon(
            onPressed: () async {
              await [Permission.photos, Permission.videos, Permission.storage]
                  .request();
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

  Widget _volTile(Volume v) {
    final sel = _selId == v.id;
    return Card(
      color: sel ? kPurple.withOpacity(0.3) : kPanel2,
      child: ListTile(
        leading: Icon(v.removable ? Icons.sd_card : Icons.smartphone,
            color: sel ? kPink : kDim),
        title: Text(v.name, style: const TextStyle(color: kText)),
        subtitle: Text(v.removable ? 'Memory card' : 'Device storage',
            style: const TextStyle(color: kDim, fontSize: 11)),
        trailing: sel ? const Icon(Icons.check_circle, color: kPink) : null,
        onTap: () => setState(() => _selId = v.id),
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
"""

DART_CUSTOMIZE = """\
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../config.dart';
import '../theme.dart';
import 'image_editor_screen.dart';

class _SlotDef {
  final String slot, title, desc;
  final double aspect;
  const _SlotDef(this.slot, this.title, this.desc, this.aspect);
}

const _slots = [
  _SlotDef('splash', 'Loading screen', 'Shows with an animation when the app opens', 1.0),
  _SlotDef('banner', 'Home banner', 'Top of the Search tab', 3.0),
  _SlotDef('background', 'App background', 'Soft image behind the search', 0.56),
  _SlotDef('empty', 'Empty state', 'Shown before you search', 1.1),
];

class CustomizeScreen extends StatefulWidget {
  const CustomizeScreen({super.key});
  @override
  State<CustomizeScreen> createState() => _CustomizeScreenState();
}

class _CustomizeScreenState extends State<CustomizeScreen> {
  final _picker = ImagePicker();

  Future<void> _pick(_SlotDef def) async {
    final x = await _picker.pickImage(source: ImageSource.gallery);
    if (x == null) return;
    if (!mounted) return;
    final path = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => ImageEditorScreen(
          sourcePath: x.path,
          aspect: def.aspect,
          slot: def.slot,
          title: def.title,
        ),
      ),
    );
    if (path != null) {
      await AppConfig.setCustomImage(def.slot, path);
      if (mounted) setState(() {});
    }
  }

  Future<void> _clear(String slot) async {
    await AppConfig.clearCustomImage(slot);
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: kBg,
        title: Text('Customize', style: TextStyle(shadows: neonShadow(kPink))),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'Pick images from your gallery and adjust them in the editor (drag and '
            'zoom) to place them exactly where you want. They stay saved inside '
            'the app even after you close it.',
            style: TextStyle(color: kDim, fontSize: 13),
          ),
          const SizedBox(height: 18),
          ..._slots.map(_slot),
        ],
      ),
    );
  }

  Widget _slot(_SlotDef def) {
    final path = AppConfig.customImage(def.slot);
    final has = path != null && File(path).existsSync();
    return Container(
      margin: const EdgeInsets.only(bottom: 18),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: kPanel,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: kPanel2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(def.title,
              style: TextStyle(
                  color: kPink2,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  shadows: neonShadow(kPink))),
          Text(def.desc, style: const TextStyle(color: kDim, fontSize: 12)),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: AspectRatio(
              aspectRatio: def.aspect < 1 ? 1.6 : def.aspect,
              child: Container(
                width: double.infinity,
                color: kPanel2,
                child: has
                    ? Image.file(File(path), fit: BoxFit.cover)
                    : const Center(
                        child: Icon(Icons.image_outlined, color: kDim, size: 46)),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                      backgroundColor: kPurple, foregroundColor: Colors.white),
                  onPressed: () => _pick(def),
                  icon: const Icon(Icons.photo_library),
                  label: Text(has ? 'Change / reposition' : 'Choose from gallery'),
                ),
              ),
              if (has) const SizedBox(width: 10),
              if (has)
                IconButton(
                  onPressed: () => _clear(def.slot),
                  icon: const Icon(Icons.delete_outline, color: kPink),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
"""

DART_PHRASES = """\
import 'dart:math';

// Lewd/ecchi lines sprinkled across the app. Cat-flavored for Kooteu ;)
const lewdPhrases = [
  'Nya~ Kooteu, come see what this kitty hid just for you 😳',
  'Download me slow... or fast, the way a curious cat likes it 💦',
  'Collect these treats and make this kitty arch her back 🔞',
  'Shhh... this stays between us cats, okay? 😈',
  'Nothing is naughtier than this search, except you, Kooteu 😏',
  'Already purring, just waiting for you to press play~',
  'Careful: spicy +18 catnip all over here 🥵',
  'Pet me... I mean, tap the image 💋',
  'One more cutie for your secret little litter 😻',
  'You are the kind of cat who likes to see it all, right Kooteu? 👀',
  'Choose well, Kooteu, this kitty earned your paws 💕',
  'Saved and curled up nice and close to you, nya~',
];

String randomLewd() => lewdPhrases[Random().nextInt(lewdPhrases.length)];
"""

DART_EDITOR = """\
import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:path_provider/path_provider.dart';
import '../theme.dart';

/// Editor simples de recorte/posicao: o usuario arrasta e da zoom na imagem
/// dentro de uma moldura com a proporcao do destino; ao salvar, captura
/// exatamente o que aparece na moldura (WYSIWYG) via RepaintBoundary.
class ImageEditorScreen extends StatefulWidget {
  final String sourcePath;
  final double aspect;
  final String slot;
  final String title;

  const ImageEditorScreen({
    super.key,
    required this.sourcePath,
    required this.aspect,
    required this.slot,
    required this.title,
  });

  @override
  State<ImageEditorScreen> createState() => _ImageEditorScreenState();
}

class _ImageEditorScreenState extends State<ImageEditorScreen> {
  final _key = GlobalKey();
  final _tc = TransformationController();
  bool _saving = false;

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await WidgetsBinding.instance.endOfFrame;
      final boundary =
          _key.currentContext!.findRenderObject() as RenderRepaintBoundary;
      final image = await boundary.toImage(pixelRatio: 3.0);
      final data = await image.toByteData(format: ui.ImageByteFormat.png);
      final dir = await getApplicationDocumentsDirectory();
      final dest = File('${dir.path}/custom_${widget.slot}.png');
      await dest.writeAsBytes(data!.buffer.asUint8List());
      if (mounted) Navigator.pop(context, dest.path);
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error saving: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: kBg,
        title: Text(widget.title, style: TextStyle(shadows: neonShadow(kPink))),
      ),
      body: Column(
        children: [
          const Padding(
            padding: EdgeInsets.all(14),
            child: Text(
              'Drag and zoom to frame it just the way it makes you purr 😏\\n'
              'Whatever shows inside the frame is what gets saved.',
              textAlign: TextAlign.center,
              style: TextStyle(color: kPink2, fontStyle: FontStyle.italic),
            ),
          ),
          Expanded(
            child: Center(
              child: LayoutBuilder(
                builder: (ctx, cons) {
                  double w = cons.maxWidth - 24;
                  double h = w / widget.aspect;
                  final maxH = cons.maxHeight - 24;
                  if (h > maxH) {
                    h = maxH;
                    w = h * widget.aspect;
                  }
                  return SizedBox(
                    width: w,
                    height: h,
                    child: Stack(
                      children: [
                        RepaintBoundary(
                          key: _key,
                          child: ClipRect(
                            child: InteractiveViewer(
                              transformationController: _tc,
                              minScale: 0.4,
                              maxScale: 6,
                              panEnabled: true,
                              scaleEnabled: true,
                              boundaryMargin: const EdgeInsets.all(double.infinity),
                              clipBehavior: Clip.none,
                              child: SizedBox(
                                width: w,
                                height: h,
                                child: Image.file(File(widget.sourcePath),
                                    fit: BoxFit.cover),
                              ),
                            ),
                          ),
                        ),
                        IgnorePointer(
                          child: Container(
                            decoration: BoxDecoration(
                              border: Border.all(color: kPink, width: 2),
                              boxShadow: [
                                BoxShadow(
                                    color: kPink.withOpacity(0.5), blurRadius: 12),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: GestureDetector(
              onTap: _saving ? null : _save,
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 16),
                decoration: glowBox(radius: 16),
                child: Center(
                  child: _saving
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2))
                      : const Text('SAVE POSITION',
                          style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 1.2)),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
"""

DART_FILES = {
    "lib/main.dart": DART_MAIN,
    "lib/theme.dart": DART_THEME,
    "lib/config.dart": DART_CONFIG,
    "lib/phrases.dart": DART_PHRASES,
    "lib/gelbooru.dart": DART_GELBOORU,
    "lib/storage.dart": DART_STORAGE,
    "lib/screens/splash_screen.dart": DART_SPLASH,
    "lib/screens/root_nav.dart": DART_ROOTNAV,
    "lib/screens/home_screen.dart": DART_HOME,
    "lib/screens/settings_screen.dart": DART_SETTINGS,
    "lib/screens/customize_screen.dart": DART_CUSTOMIZE,
    "lib/screens/image_editor_screen.dart": DART_EDITOR,
    "lib/widgets/image_card.dart": DART_IMAGECARD,
}


# ═══════════════════════════════════════════════════════
#  FLUTTER — ENCONTRAR / INSTALAR
# ═══════════════════════════════════════════════════════

def _flutter_exe(flutter_dir: Path) -> Path:
    return flutter_dir / "bin" / ("flutter.bat" if IS_WINDOWS else "flutter")

def _clone_valido(flutter_dir: Path) -> bool:
    return (flutter_dir / ".git").is_dir() and _flutter_exe(flutter_dir).exists()

def _flutter_funciona(cmd: str) -> bool:
    try:
        result = subprocess.run(f'"{cmd}" --version', shell=IS_WINDOWS,
                                capture_output=True, text=True, timeout=120,
                                encoding='utf-8', errors='replace')
        return "not a clone" not in (result.stdout + result.stderr)
    except subprocess.TimeoutExpired:
        return True
    except Exception:
        return False

def _clonar_flutter():
    if FLUTTER_DIR.exists():
        aviso(f"Removendo instalacao anterior: {FLUTTER_DIR}")
        shutil.rmtree(FLUTTER_DIR, ignore_errors=True)
    info(f"Clonando Flutter em: {FLUTTER_DIR} (pode demorar na primeira vez)")
    result = subprocess.run(
        f'git clone --depth 1 -b stable https://github.com/flutter/flutter.git "{FLUTTER_DIR}"',
        shell=IS_WINDOWS)
    if result.returncode != 0:
        erro("Falha ao clonar Flutter.")
        sys.exit(1)
    ok("Flutter clonado.")

def verificar_flutter() -> str:
    titulo("Verificando Flutter SDK")
    if _clone_valido(FLUTTER_DIR):
        exe = str(_flutter_exe(FLUTTER_DIR))
        ok(f"Flutter (git clone): {FLUTTER_DIR}")
        os.environ["PATH"] = str(FLUTTER_DIR / "bin") + os.pathsep + os.environ.get("PATH", "")
        return exe
    system_flutter = shutil.which("flutter") or shutil.which("flutter.bat")
    if system_flutter and _flutter_funciona(system_flutter):
        ok(f"Flutter do sistema OK: {system_flutter}")
        return system_flutter
    aviso("Flutter nao encontrado/instavel — clonando via Git...")
    _clonar_flutter()
    exe = str(_flutter_exe(FLUTTER_DIR))
    os.environ["PATH"] = str(FLUTTER_DIR / "bin") + os.pathsep + os.environ.get("PATH", "")
    ok(f"Flutter pronto: {exe}")
    return exe


def verificar_git() -> bool:
    titulo("Verificando Git")
    if shutil.which("git"):
        ok("Git encontrado")
        return True
    erro("Git nao encontrado — obrigatorio para clonar o Flutter.")
    return False


def verificar_java() -> bool:
    titulo("Verificando Java / JDK")
    if shutil.which("java"):
        ok("Java encontrado")
        return True
    aviso("Java nao encontrado no PATH.")
    info("Baixe o JDK 17 em: https://adoptium.net/ (marque 'Add to PATH').")
    try:
        resp = input("  Cole o caminho da pasta 'bin' do Java (ou Enter para sair): ").strip()
    except EOFError:
        resp = ""
    if resp and Path(resp).exists():
        os.environ["PATH"] = resp + os.pathsep + os.environ.get("PATH", "")
        if shutil.which("java"):
            ok("Java configurado.")
            return True
    return False


def verificar_android_sdk() -> bool:
    titulo("Verificando Android SDK")
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        candidatos = []
        if IS_WINDOWS:
            candidatos = [Path.home() / "AppData" / "Local" / "Android" / "Sdk",
                          Path("C:/Android/Sdk")]
        elif IS_MAC:
            candidatos = [Path.home() / "Library" / "Android" / "sdk"]
        else:
            candidatos = [Path.home() / "Android" / "Sdk"]
        for p in candidatos:
            if p.exists():
                sdk = str(p); break
    if sdk and Path(sdk).exists():
        os.environ["ANDROID_HOME"] = sdk
        os.environ["ANDROID_SDK_ROOT"] = sdk
        ok(f"Android SDK: {sdk}")
        return True
    aviso("Android SDK nao encontrado. Instale o Android Studio.")
    return False


def aceitar_licencas(flutter_cmd: str):
    titulo("Aceitando licencas Android SDK")
    try:
        proc = subprocess.Popen(f'"{flutter_cmd}" doctor --android-licenses',
                                shell=IS_WINDOWS, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8', errors='replace')
        proc.communicate(input='y\n' * 12, timeout=120)
        ok("Licencas aceitas.")
    except Exception as e:
        aviso(f"Licencas: {e}")


# ═══════════════════════════════════════════════════════
#  CRIAR PROJETO + ESCREVER ARQUIVOS
# ═══════════════════════════════════════════════════════

def criar_projeto(flutter_cmd: str):
    titulo("Criando projeto Flutter base")
    gradle_wrapper = PROJECT_DIR / "android" / "gradle" / "wrapper" / "gradle-wrapper.jar"
    if IS_CLEAN and PROJECT_DIR.exists():
        info("--clean: removendo projeto existente...")
        shutil.rmtree(PROJECT_DIR, ignore_errors=True)
    if not gradle_wrapper.exists():
        info("Executando flutter create...")
        result = subprocess.run(
            f'"{flutter_cmd}" create --org {ORG} --project-name {PROJECT_NAME} '
            f'--platforms android "{PROJECT_DIR}"',
            shell=IS_WINDOWS, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            erro("flutter create falhou.")
            sys.exit(1)
        ok("Projeto base criado.")
    else:
        ok("Projeto base ja existe.")


def escrever_arquivo(caminho: Path, conteudo: str):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding='utf-8')


def _limpar_kotlin_dir():
    """Remove MainActivity gerado em qualquer pacote pra evitar duplicata."""
    kotlin_root = PROJECT_DIR / "android" / "app" / "src" / "main" / "kotlin"
    if kotlin_root.exists():
        for f in kotlin_root.rglob("MainActivity.kt"):
            try:
                f.unlink()
            except Exception:
                pass


def escrever_arquivos_customizados():
    titulo("Aplicando arquivos do GelDroid")

    for old in ["settings.gradle", "build.gradle", "app/build.gradle"]:
        p = PROJECT_DIR / "android" / old
        if p.exists():
            p.unlink()
            info(f"Removido Groovy: {old}")

    escrever_arquivo(PROJECT_DIR / "pubspec.yaml", PUBSPEC_YAML)
    escrever_arquivo(PROJECT_DIR / "android" / "settings.gradle.kts", SETTINGS_GRADLE_KTS)
    escrever_arquivo(PROJECT_DIR / "android" / "build.gradle.kts", ROOT_BUILD_GRADLE_KTS)
    escrever_arquivo(PROJECT_DIR / "android" / "app" / "build.gradle.kts", APP_BUILD_GRADLE_KTS)
    escrever_arquivo(PROJECT_DIR / "android" / "gradle.properties", GRADLE_PROPERTIES)
    escrever_arquivo(
        PROJECT_DIR / "android" / "app" / "src" / "main" / "AndroidManifest.xml",
        ANDROID_MANIFEST)

    _limpar_kotlin_dir()
    escrever_arquivo(
        PROJECT_DIR / "android" / "app" / "src" / "main" / "kotlin" /
        "com" / "geldroid" / "geldroid" / "MainActivity.kt",
        MAIN_ACTIVITY_KT)

    for rel, content in DART_FILES.items():
        escrever_arquivo(PROJECT_DIR / rel, content)

    # styles / launch background (garante existencia)
    styles = PROJECT_DIR / "android" / "app" / "src" / "main" / "res" / "values" / "styles.xml"
    if not styles.exists():
        escrever_arquivo(styles, """\
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="LaunchTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">@drawable/launch_background</item>
    </style>
    <style name="NormalTheme" parent="@android:style/Theme.Black.NoTitleBar">
        <item name="android:windowBackground">?android:colorBackground</item>
    </style>
</resources>
""")
    launch_bg = PROJECT_DIR / "android" / "app" / "src" / "main" / "res" / "drawable" / "launch_background.xml"
    if not launch_bg.exists():
        escrever_arquivo(launch_bg, """\
<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@android:color/black" />
</layer-list>
""")

    ok("pubspec.yaml + lib/*.dart + gradle + manifest + MainActivity.kt")


# ═══════════════════════════════════════════════════════
#  ICONE (coracao rosa lewd)
# ═══════════════════════════════════════════════════════

def instalar_pillow() -> bool:
    try:
        import PIL  # noqa
        return True
    except ImportError:
        r = subprocess.run(f'"{sys.executable}" -m pip install Pillow --quiet',
                           shell=IS_WINDOWS, capture_output=True, text=True)
        return r.returncode == 0


def gerar_icone() -> bool:
    titulo("Gerando icone")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    icon_path = ASSETS_DIR / "icon.png"
    if not instalar_pillow():
        aviso("Pillow indisponivel; usando icone padrao.")
        return False
    try:
        from PIL import Image, ImageDraw

        S = 512
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, S, S], radius=118, fill=(20, 8, 22, 255))

        def heart(cx, cy, size, color):
            r = size * 0.30
            d.ellipse([cx - size * 0.52, cy - size * 0.40,
                       cx - size * 0.52 + 2 * r, cy - size * 0.40 + 2 * r], fill=color)
            d.ellipse([cx + size * 0.52 - 2 * r, cy - size * 0.40,
                       cx + size * 0.52, cy - size * 0.40 + 2 * r], fill=color)
            d.polygon([(cx - size * 0.60, cy - size * 0.02),
                       (cx + size * 0.60, cy - size * 0.02),
                       (cx, cy + size * 0.62)], fill=color)

        # glow
        for i in range(10, 0, -1):
            a = int(22 * i / 10)
            heart(S / 2, S / 2 + 10, 180 + i * 6, (255, 79, 139, a))
        # corpo
        heart(S / 2, S / 2 + 10, 180, (255, 79, 139, 255))
        heart(S / 2, S / 2 + 10, 168, (255, 120, 170, 255))
        # brilho
        d.ellipse([S * 0.36, S * 0.30, S * 0.46, S * 0.40], fill=(255, 230, 240, 150))

        img.save(str(icon_path), "PNG")
        ok(f"Icone gerado: {icon_path}")
        return True
    except Exception as e:
        aviso(f"Erro ao gerar icone: {e}")
        return False


# ═══════════════════════════════════════════════════════
#  PATCHES NO PUB CACHE (compatibilidade Gradle/AGP novos)
# ═══════════════════════════════════════════════════════

def _pub_cache():
    candidates = [
        Path.home() / ".pub-cache" / "hosted" / "pub.dev",
        Path.home() / "AppData" / "Local" / "Pub" / "Cache" / "hosted" / "pub.dev",
        Path(os.environ.get("PUB_CACHE", "____")) / "hosted" / "pub.dev",
    ]
    return next((p for p in candidates if p.exists()), None)


def patch_compilesdk():
    titulo("Corrigindo compileSdk de plugins")
    pc = _pub_cache()
    if pc is None:
        aviso("Pub cache nao localizado — pulando.")
        return
    patched = []
    for plugin_dir in pc.iterdir():
        gf = plugin_dir / "android" / "build.gradle"
        if not gf.exists():
            continue
        try:
            original = gf.read_text(encoding='utf-8', errors='replace')
            updated = original
            for sdk in range(21, 36):
                updated = updated.replace(f'compileSdkVersion {sdk}', 'compileSdkVersion 36')
                updated = updated.replace(f'compileSdk {sdk}', 'compileSdk 36')
                updated = updated.replace(f'compileSdk = {sdk}', 'compileSdk = 36')
                updated = updated.replace(f'compileSdkVersion = {sdk}', 'compileSdkVersion = 36')
            if updated != original:
                gf.write_text(updated, encoding='utf-8')
                patched.append(plugin_dir.name)
        except Exception:
            pass
    info(f"{len(patched)} plugin(s) ajustado(s).")


def _remove_registrar_method(content: str) -> str:
    lines = content.split('\n')
    result = []
    in_method = False
    depth = 0
    for line in lines:
        if not in_method:
            s = line.strip()
            if ('registerWith' in s and ('Registrar' in s or 'PluginRegistrantCallback' in s)):
                in_method = True
                depth = line.count('{') - line.count('}')
                result.append('    // registerWith(Registrar) removido (v1 embedding)')
                if depth <= 0:
                    in_method = False
                continue
        else:
            depth += line.count('{') - line.count('}')
            if depth <= 0:
                in_method = False
            continue
        result.append(line)
    return '\n'.join(result)


def patch_v1_embedding():
    titulo("Corrigindo v1 embedding em plugins Java")
    pc = _pub_cache()
    if pc is None:
        aviso("Pub cache nao localizado — pulando.")
        return
    markers = ['PluginRegistry.Registrar', 'ShimPluginRegistry',
               'FlutterNativeView', 'PluginRegistrantCallback']
    v1_classes = [
        'io.flutter.embedding.engine.plugins.shim.ShimPluginRegistry',
        'io.flutter.view.FlutterNativeView',
        'io.flutter.plugin.common.PluginRegistry.PluginRegistrantCallback',
        'io.flutter.plugin.common.PluginRegistry.Registrar',
    ]
    patched = set()
    for jf in pc.rglob("*.java"):
        try:
            original = jf.read_text(encoding='utf-8', errors='replace')
            if not any(m in original for m in markers):
                continue
            updated = _remove_registrar_method(original)
            for cls in v1_classes:
                updated = updated.replace(f'import {cls};', f'// import {cls};')
            if updated != original:
                jf.write_text(updated, encoding='utf-8')
                patched.add(jf.parts[len(pc.parts)])
        except Exception:
            pass
    info(f"{len(patched)} plugin(s) ajustado(s).")


# ═══════════════════════════════════════════════════════
#  PUB GET + ICONS + BUILD
# ═══════════════════════════════════════════════════════

def pub_get(flutter_cmd: str):
    titulo("Instalando dependencias (flutter pub get)")
    result = subprocess.run(f'"{flutter_cmd}" pub get', shell=IS_WINDOWS,
                            cwd=str(PROJECT_DIR), encoding='utf-8', errors='replace')
    if result.returncode != 0:
        erro("flutter pub get falhou.")
        sys.exit(1)
    ok("Dependencias instaladas.")


def gerar_launcher_icons(flutter_cmd: str):
    titulo("Gerando launcher icons")
    if not (ASSETS_DIR / "icon.png").exists():
        aviso("icon.png nao encontrado, pulando.")
        return
    result = subprocess.run(f'"{flutter_cmd}" pub run flutter_launcher_icons',
                            shell=IS_WINDOWS, cwd=str(PROJECT_DIR),
                            capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode == 0:
        ok("Launcher icons gerados.")
    else:
        aviso("Launcher icons: erro nao critico.")


def buildar_apk(flutter_cmd: str) -> bool:
    modo = "debug" if IS_DEBUG else "release"
    titulo(f"Construindo APK ({modo})")
    info("Primeira compilacao pode levar alguns minutos...")
    cmd = f'"{flutter_cmd}" build apk'
    cmd += ' --debug' if IS_DEBUG else ' --release --target-platform android-arm64'
    result = subprocess.run(cmd, shell=IS_WINDOWS, cwd=str(PROJECT_DIR),
                            encoding='utf-8', errors='replace')
    return result.returncode == 0


def copiar_apk():
    titulo("Localizando APK")
    candidatos = [
        PROJECT_DIR / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk",
        PROJECT_DIR / "build" / "app" / "outputs" / "flutter-apk" / "app-debug.apk",
    ]
    apk = next((p for p in candidatos if p.exists()), None)
    if not apk:
        for f in PROJECT_DIR.rglob("*.apk"):
            apk = f
            break
    if apk:
        dest = SCRIPT_DIR / "GelDroid.apk"
        shutil.copy2(apk, dest)
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"""
{VERDE}{NEGRITO}{'='*60}{RESET}
{VERDE}{NEGRITO}  APK gerado com sucesso!{RESET}

  {NEGRITO}Arquivo:{RESET} {VERDE}{dest}{RESET}
  {NEGRITO}Tamanho:{RESET} {size_mb:.1f} MB

  {NEGRITO}Instalar via USB (adb):{RESET}
    adb install "{dest}"

  {NEGRITO}Ou transfira o APK pro celular e instale manualmente.{RESET}
{VERDE}{NEGRITO}{'='*60}{RESET}
""")
        if IS_WINDOWS:
            subprocess.run(f'explorer /select,"{dest}"', shell=True)
        return str(dest)
    erro("APK nao encontrado apos o build.")
    return None


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    print(f"""{NEGRITO}{CIANO}
   ____      _ ____            _     _
  / ___| ___| |  _ \\ _ __ ___ (_) __| |
 | |  _ / _ \\ | | | | '__/ _ \\| |/ _` |
 | |_| |  __/ | |_| | | | (_) | | (_| |
  \\____|\\___|_|____/|_|  \\___/|_|\\__,_|
        Gelbooru -> Galeria  |  Build v1.0
{RESET}""")

    info(f"Projeto: {PROJECT_DIR}")
    info(f"Modo: {'DEBUG' if IS_DEBUG else 'RELEASE'}")
    info(f"Sistema: {platform.system()} {platform.machine()}")

    if not verificar_git():
        sys.exit(1)
    if not verificar_java():
        erro("Instale o JDK 17 e rode de novo.")
        sys.exit(1)
    android_ok = verificar_android_sdk()
    flutter_cmd = verificar_flutter()
    if android_ok:
        aceitar_licencas(flutter_cmd)

    criar_projeto(flutter_cmd)
    escrever_arquivos_customizados()
    gerar_icone()
    pub_get(flutter_cmd)
    patch_compilesdk()
    patch_v1_embedding()
    gerar_launcher_icons(flutter_cmd)

    if buildar_apk(flutter_cmd):
        if not copiar_apk():
            sys.exit(1)
    else:
        titulo("FALHA NO BUILD")
        print(f"""
{AMARELO}  Para ver detalhes, rode manualmente:{RESET}
  cd "{PROJECT_DIR}"
  "{flutter_cmd}" build apk --release
""")
        sys.exit(1)


if __name__ == "__main__":
    main()
