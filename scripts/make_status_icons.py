"""Render crisp waveform icons for the menu bar from vector paths."""
from pathlib import Path
import AppKit as AK

output = Path('assets/status')
output.mkdir(parents=True, exist_ok=True)
for state, color in {
    'idle': (0, 0, 0),
    'recording': (0.95, 0.20, 0.25),
    'processing': (0.95, 0.57, 0.08),
}.items():
    bitmap = AK.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, 128, 128, 8, 4, True, False, AK.NSDeviceRGBColorSpace, 0, 0)
    AK.NSGraphicsContext.saveGraphicsState()
    AK.NSGraphicsContext.setCurrentContext_(AK.NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap))
    AK.NSColor.colorWithCalibratedRed_green_blue_alpha_(*color, 1).setFill()
    for index, height in enumerate((22, 44, 72, 100, 64, 42, 20)):
        AK.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
            ((10 + index * 16, (128 - height) / 2), (12, height)), 6, 6).fill()
    AK.NSGraphicsContext.restoreGraphicsState()
    bitmap.representationUsingType_properties_(AK.NSBitmapImageFileTypePNG, {}).writeToFile_atomically_(
        str(output / f'{state}.png'), True)
