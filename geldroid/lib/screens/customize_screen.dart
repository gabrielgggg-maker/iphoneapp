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
