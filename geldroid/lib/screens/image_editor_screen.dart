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
              'Drag and zoom to frame it just the way it makes you purr 😏\n'
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
