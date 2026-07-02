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
        volumeId: 'internal',
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
