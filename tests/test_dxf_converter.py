"""tests/test_dxf_converter.py — dxf_converter 集成测试"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def make_simple_dxf(path):
    """生成一个最小的 DXF 文件用于测试"""
    import ezdxf
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 100))
    msp.add_circle((50, 50), radius=20)
    doc.saveas(path)


def test_render_dxf_to_png():
    from app.utils.dxf_converter import render_dxf_to_png
    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = os.path.join(tmpdir, 'test.dxf')
        make_simple_dxf(dxf_path)
        results = render_dxf_to_png(dxf_path, tmpdir, 'test', max_dims=[500, 1000])
        assert '500' in results
        assert '1000' in results
        for dim, info in results.items():
            assert os.path.exists(os.path.join(tmpdir, info['filename']))
            assert info['width'] > 0 and info['height'] > 0
    print('test_render_dxf_to_png PASSED')


def test_combine_dxf_with_image():
    from app.utils.dxf_converter import combine_dxf_with_image
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = os.path.join(tmpdir, 'test.dxf')
        make_simple_dxf(dxf_path)
        png_path = os.path.join(tmpdir, 'canvas.png')
        img = Image.new('RGBA', (800, 600), (255, 0, 0, 128))
        img.save(png_path)
        out_dxf = os.path.join(tmpdir, 'output.dxf')
        result = combine_dxf_with_image(dxf_path, png_path, out_dxf, 297, 210)
        assert os.path.exists(out_dxf)
        import ezdxf
        doc = ezdxf.readfile(out_dxf)
        layer_names = {layer.dxf.name for layer in doc.layers}
        assert 'BACKGROUND' in layer_names, f"缺少 BACKGROUND 图层，有: {layer_names}"
        assert 'SYSTEM_DESIGN' in layer_names, f"缺少 SYSTEM_DESIGN 图层，有: {layer_names}"
    print('test_combine_dxf_with_image PASSED')


if __name__ == '__main__':
    test_render_dxf_to_png()
    test_combine_dxf_with_image()
    print('All tests passed')
