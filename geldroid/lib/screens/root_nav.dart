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
