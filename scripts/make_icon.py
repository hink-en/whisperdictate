"""Render the app's simple vector microphone icon into a macOS icon set."""
from pathlib import Path
import subprocess
import AppKit as AK

output = Path('build/WhisperDictate.iconset')
output.mkdir(parents=True, exist_ok=True)
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        pixels = size * scale
        bitmap = AK.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
            None, pixels, pixels, 8, 4, True, False, AK.NSDeviceRGBColorSpace, 0, 0)
        context = AK.NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap)
        AK.NSGraphicsContext.saveGraphicsState()
        AK.NSGraphicsContext.setCurrentContext_(context)
        factor = pixels / 1024
        transform = AK.NSAffineTransform.transform()
        transform.scaleBy_(factor)
        transform.concat()
        AK.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.07, 0.36, 0.34, 1).setFill()
        AK.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(((56, 56), (912, 912)), 210, 210).fill()
        AK.NSColor.whiteColor().setFill()
        AK.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(((410, 415), (204, 360)), 102, 102).fill()
        AK.NSColor.whiteColor().setStroke()
        path = AK.NSBezierPath.bezierPath()
        path.setLineWidth_(48)
        path.setLineCapStyle_(AK.NSRoundLineCapStyle)
        path.moveToPoint_((320, 535))
        path.lineToPoint_((320, 465))
        path.curveToPoint_controlPoint1_controlPoint2_((704, 465), (320, 220), (704, 220))
        path.lineToPoint_((704, 535))
        path.stroke()
        stem = AK.NSBezierPath.bezierPath()
        stem.setLineWidth_(48)
        stem.setLineCapStyle_(AK.NSRoundLineCapStyle)
        stem.moveToPoint_((512, 290))
        stem.lineToPoint_((512, 215))
        stem.moveToPoint_((422, 215))
        stem.lineToPoint_((602, 215))
        stem.stroke()
        AK.NSGraphicsContext.restoreGraphicsState()
        suffix = '@2x' if scale == 2 else ''
        data = bitmap.representationUsingType_properties_(AK.NSBitmapImageFileTypePNG, {})
        data.writeToFile_atomically_(str(output / f'icon_{size}x{size}{suffix}.png'), True)
subprocess.run(['iconutil', '-c', 'icns', str(output), '-o', 'assets/WhisperDictate.icns'], check=True)
