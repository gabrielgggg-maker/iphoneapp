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
