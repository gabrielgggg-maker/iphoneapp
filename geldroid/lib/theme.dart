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
