import 'dart:io';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../config.dart';
import '../phrases.dart';
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
    await Future.delayed(const Duration(milliseconds: 1600));
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const RootNav()),
    );
  }

  Future<void> _perms() async {
    await [Permission.photos, Permission.storage].request();
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
