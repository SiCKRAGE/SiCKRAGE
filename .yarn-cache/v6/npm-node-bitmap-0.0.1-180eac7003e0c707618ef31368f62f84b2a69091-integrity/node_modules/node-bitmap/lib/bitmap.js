var Bitmap = module.exports = exports = function(buffer){
  this.buffer = buffer;
  this.initialized = false;

  this.fileHeader = null;
  this.infoHeader = null;
  this.coreHeader = null;
  this.colorPalette = null;
  this.dataPos = -1;
};
Bitmap.prototype.CORE_TYPE_WINDOWS_V3 = 40;
Bitmap.prototype.CORE_TYPE_WINDOWS_V4 = 108;
Bitmap.prototype.CORE_TYPE_WINDOWS_V5 = 124;
Bitmap.prototype.CORE_TYPE_OS2_V1 = 12;
Bitmap.prototype.CORE_TYPE_OS2_V2 = 64;
Bitmap.prototype.BITMAPCOREHEADER = Bitmap.prototype.CORE_TYPE_OS2_V1;
Bitmap.prototype.BITMAPINFOHEADER = Bitmap.prototype.CORE_TYPE_WINDOWS_V3;
Bitmap.prototype.BITMAPINFOHEADER2 = Bitmap.prototype.CORE_TYPE_OS2_V2;
Bitmap.prototype.BITMAPV4HEADER = Bitmap.prototype.CORE_TYPE_WINDOWS_V4;
Bitmap.prototype.BITMAPV5HEADER = Bitmap.prototype.CORE_TYPE_WINDOWS_V5;
Bitmap.prototype.COMPRESSION_BI_RGB = 0;
Bitmap.prototype.COMPRESSION_BI_RLE8 = 1;
Bitmap.prototype.COMPRESSION_BI_RLE4 = 2;
Bitmap.prototype.COMPRESSION_BI_BITFIELDS = 3;
Bitmap.prototype.COMPRESSION_BI_JPEG = 4;
Bitmap.prototype.COMPRESSION_BI_PNG = 5;
Bitmap.prototype.BITCOUNT_2 = 1;
Bitmap.prototype.BITCOUNT_16 = 4;
Bitmap.prototype.BITCOUNT_256 = 8;
Bitmap.prototype.BITCOUNT_16bit = 16;
Bitmap.prototype.BITCOUNT_24bit = 24;
Bitmap.prototype.BITCOUNT_32bit = 32;
Bitmap.prototype.init = function(){
  this.readFileHeader();
  this.readInfoHeader();
  this.readCoreHeader();
  this.readColorPalette();

  this.initDataPos();
  this.initialized = true;
};
Bitmap.prototype.checkInit = function (){
  if(!this.initialized){
    throw new Error('not initialized');
  }
  /* nop */
};
Bitmap.prototype.isBitmap = function(){
  this.checkInit();

  if('BM' == this.fileHeader.bfType){
    return true;
  }
  return false;
};
Bitmap.prototype.getData = function (){
  this.checkInit();

  if(this.COMPRESSION_BI_RGB !== this.coreHeader.__copmression__){
    throw new Error('not supported compression: ' + this.coreHeader.__copmression__);
  }

  var bitCount = this.coreHeader.__bitCount__;
  var width = this.getWidth();
  var height = this.getHeight();

  var line = (width * bitCount) / 8;
  if(0 != (line % 4)){
    line = ((line / 4) + 1) * 4;
  }

  var rgbaData = [];
  var dataPos = this.dataPos;
  for(var i = 0; i < height; ++i) {
    var pos = dataPos + (line * (height - (i + 1)));
    var buf = this.buffer.slice(pos, pos + line);
    var color = this.mapColor(buf, bitCount);
    rgbaData.push(color);
  }
  return rgbaData;
};
Bitmap.prototype.getWidth = function (){
  this.checkInit();

  return this.coreHeader.__width__;
};
Bitmap.prototype.getHeight = function (){
  this.checkInit();

  return this.coreHeader.__height__;
};
Bitmap.prototype.read = function(buf, offset, limit){
  var read = [];
  for(var i = offset, len = offset + limit; i < len; ++i){
    read.push(buf.readInt8(i));
  }
  return new Buffer(read);
};
Bitmap.prototype.readFileHeader = function(){
  var bfType = this.read(this.buffer, 0, 2);
  var bfSize = this.read(this.buffer, 2, 4);
  var bfReserved1 = this.read(this.buffer, 6, 2);
  var bfReserved2 = this.read(this.buffer, 8, 2);
  var bfOffBits = this.read(this.buffer, 10, 4);

  this.fileHeader = {
    bfType: bfType.toString('ascii'),
    _bfType: bfType,
    bfSize: bfSize.readUInt16LE(0),
    _bfSize: bfSize,
    bfReserved1: 0,
    bfReserved2: 0,
    bfOffBits: bfOffBits.readUInt16LE(0),
    _bfOffBits: bfOffBits
  };
};
Bitmap.prototype.readInfoHeader = function (){
  this.infoHeader = this.read(this.buffer, 14, 4);
};
Bitmap.prototype.readCoreHeader = function (){
  var coreType = this.infoHeader.readUInt16LE(0);
  switch(coreType){
  case this.BITMAPCOREHEADER:
    return this.readCoreHeaderOS2_V1();
  case this.BITMAPINFOHEADER2:
    return this.readCoreHeaderOS2_V2();
  case this.BITMAPV4HEADER:
    return this.readCoreHeaderWINDOWS_V4();
  case this.BITMAPV5HEADER:
    return this.readCoreHeaderWINDOWS_V5();
  case this.BITMAPINFOHEADER:
    return this.readCoreHeaderWINDOWS_V3();
  default:
    throw new Error('unknown coreType: ' + coreType);
  }
};
Bitmap.prototype.readCoreHeaderWINDOWS_V3 = function (){
  var biWidth = this.read(this.buffer, 0x12, 4);
  var biHeight = this.read(this.buffer, 0x16, 4);
  var biPlanes = this.read(this.buffer, 0x1a, 2);
  var biBitCount = this.read(this.buffer, 0x1c, 2);
  var biCopmression = this.read(this.buffer, 0x1e, 4);
  var biSizeImage = this.read(this.buffer, 0x22, 4);
  var biXPixPerMeter = this.read(this.buffer, 0x26, 4);
  var biYPixPerMeter = this.read(this.buffer, 0x2a, 4);
  var biClrUsed = this.read(this.buffer, 0x2e, 4);
  var biCirImportant = this.read(this.buffer, 0x32, 4);

  this.coreHeader = {
    __copmression__: biCopmression.readUInt16LE(0),
    __bitCount__: biBitCount.readUInt8(0),
    __width__: biWidth.readUInt16LE(0),
    __height__: biHeight.readUInt16LE(0),
    biWidth: biWidth.readUInt16LE(0),
    _biWidth: biWidth,
    biHeight: biHeight.readUInt16LE(0),
    _biHeight: biHeight,
    biPlanes: biPlanes.readUInt8(0),
    _biPlanes: biPlanes,
    biBitCount: biBitCount.readUInt8(0),
    _biBitCount: biBitCount,
    biCopmression: biCopmression.readUInt16LE(0),
    _biCopmression: biCopmression,
    biSizeImage: biSizeImage.readUInt16LE(0),
    _biSizeImage: biSizeImage,
    biXPixPerMeter: biXPixPerMeter.readUInt16LE(0),
    _biXPixPerMeter: biXPixPerMeter,
    biYPixPerMeter: biYPixPerMeter.readUInt16LE(0),
    _biYPixPerMeter: biYPixPerMeter,
    biClrUsed: biClrUsed.readUInt16LE(0),
    _biClrUsed: biClrUsed,
    biCirImportant: biCirImportant.readUInt16LE(0),
    _biCirImportant: biCirImportant
  };
};
Bitmap.prototype.readCoreHeaderWINDOWS_V4 = function (){
  throw new Error('not yet impl');
  
  var bV4Width = this.read(this.buffer, 0x12, 4);
  var bV4Height = this.read(this.buffer, 0x16, 4);
  var bV4Planes = this.read(this.buffer, 0x1a, 2);
  var bV4BitCount = this.read(this.buffer, 0x1c, 2);
  var bV4Compression = this.read(this.buffer, 0x1e, 4);
  var bV4SizeImage = this.read(this.buffer, 0x22, 4);
  var bV4XPelsPerMeter = this.read(this.buffer, 0x26, 4);
  var bV4YPelsPerMeter = this.read(this.buffer, 0x2a, 4);
  var bV4ClrUsed = this.read(this.buffer, 0x2e, 4);
  var bV4ClrImportant = this.read(this.buffer, 0x32, 4);
  var bV4RedMask = this.read(this.buffer, 0x36, 4);
  var bV4GreenMask = this.read(this.buffer, 0x3a, 4);
  var bV4BlueMask = this.read(this.buffer, 0x3e, 4);
  var bV4AlphaMask = this.read(this.buffer, 0x42, 4);
  var bV4CSType = this.read(this.buffer, 0x46, 4);
  var bV4Endpoints = this.read(this.buffer, 0x6a, 36);
  var bV4GammaRed = this.read(this.buffer, 0x6e, 4);
  var bV4GammaGreen = this.read(this.buffer, 0x72, 4);
  var bV4GammaBlue = this.read(this.buffer, 0x76, 4);

  this.coreHeader = {
    __compression__: bV4Compression.readUInt16LE(0),
    __bitCount__: bV4BitCount.readUInt8(0),
    __width__: bV4Width.readUInt16LE(0),
    __height__: bV4Height.readUInt16LE(0),
    bV4Width: bV4Width.readUInt16LE(0),
    _bV4Width: bV4Width,
    bV4Height: bV4Height.readUInt16LE(0),
    _bV4Height: bV4Height,
    bV4Planes: bV4Planes.readUInt8(0),
    _bV4Planes: bV4Planes,
    bV4BitCount: bV4BitCount.readUInt8(0),
    _bV4BitCount: bV4BitCount,
    bV4Compression: bV4Compression.readUInt16LE(0),
    _bV4Compression: bV4Compression,
    bV4SizeImage: bV4SizeImage.readUInt16LE(0),
    _bV4SizeImage: bV4SizeImage,
    bV4XPelsPerMeter: bV4XPelsPerMeter.readUInt16LE(0),
    _bV4XPelsPerMeter: bV4XPelsPerMeter,
    bV4YPelsPerMeter: bV4YPelsPerMeter.readUInt16LE(0),
    _bV4YPelsPerMeter: bV4YPelsPerMeter,
    bV4ClrUsed: bV4ClrUsed.readUInt16LE(0),
    _bV4ClrUsed: bV4ClrUsed,
    bV4ClrImportant: bV4ClrImportant.readUInt16LE(0),
    _bV4ClrImportant: bV4ClrImportant,
    bV4RedMask: bV4RedMask.readUInt16LE(0),
    _bV4RedMask: bV4RedMask,
    bV4GreenMask: bV4GreenMask.readUInt16LE(0),
    _bV4GreenMask: bV4GreenMask,
    bV4BlueMask: bV4BlueMask.readUInt16LE(0),
    _bV4BlueMask: bV4BlueMask,
    bV4AlphaMask: bV4AlphaMask.readUInt16LE(0),
    _bV4AlphaMask: bV4AlphaMask,
    bV4CSType: bV4CSType.readUInt16LE(0),
    _bV4CSType: bV4CSType,
    bV4Endpoints: null,
    _bV4Endpoints: bV4Endpoints,
    bV4GammaRed: bV4GammaRed.readUInt16LE(0),
    _bV4GammaRed: bV4GammaRed,
    bV4GammaGreen: bV4GammaGreen.readUInt16LE(0),
    _bV4GammaGreen: bV4GammaGreen,
    bV4GammaBlue: bV4GammaBlue.readUInt16LE(0),
    _bV4GammaBlue: bV4GammaBlue
  };
};
Bitmap.prototype.readCoreHeaderWINDOWS_V5 = function (){
  throw new Error('not yet impl');

  var bV5Width = this.read(this.buffer, 0x12, 4);
  var bV5Height = this.read(this.buffer, 0x16, 4);
  var bV5Planes = this.read(this.buffer, 0x1a, 2);
  var bV5BitCount = this.read(this.buffer, 0x1c, 2);
  var bV5Compression = this.read(this.buffer, 0x1e, 4);
  var bV5SizeImage = this.read(this.buffer, 0x22, 4);
  var bV5XPelsPerMeter = this.read(this.buffer, 0x26, 4);
  var bV5YPelsPerMeter = this.read(this.buffer, 0x2a, 4);
  var bV5ClrUsed = this.read(this.buffer, 0x2e, 4);
  var bV5ClrImportant = this.read(this.buffer, 0x32, 4);
  var bV5RedMask = this.read(this.buffer, 0x36, 4);
  var bV5GreenMask = this.read(this.buffer, 0x3a, 4);
  var bV5BlueMask = this.read(this.buffer, 0x3e, 4);
  var bV5AlphaMask = this.read(this.buffer, 0x42, 4);
  var bV5CSType = this.read(this.buffer, 0x46, 4);
  var bV5Endpoints = this.read(this.buffer, 0x6a, 36);
  var bV5GammaRed = this.read(this.buffer, 0x6e, 4);
  var bV5GammaGreen = this.read(this.buffer, 0x72, 4);
  var bV5GammaBlue = this.read(this.buffer, 0x76, 4);
  var bV5Intent = this.read(this.buffer, 0x7a, 4);
  var bV5ProfileData = this.read(this.buffer, 0x7e, 4);
  var bV5ProfileSize = this.read(this.buffer, 0x82, 4);
  var bV5Reserved = this.read(this.buffer, 0x86, 4);

  this.coreHeader = {
    __compression__: bV5Compression.readUInt16LE(0),
    __bitCount__: bV5BitCount.readUInt8(0),
    __width__: bV5Width.readUInt16LE(0),
    __height__: bV5Height.readUInt16LE(0),
    bV5Width: bV5Width.readUInt16LE(0),
    _bV5Width: bV5Width,
    bV5Height: bV5Height.readUInt16LE(0),
    _bV5Height: bV5Height,
    bV5Planes: bV5Planes.readUInt8(0),
    _bV5Planes: bV5Planes,
    bV5BitCount: bV5BitCount.readUInt8(0),
    _bV5BitCount: bV5BitCount,
    bV5Compression: bV5Compression.readUInt16LE(0),
    _bV5Compression: bV5Compression,
    bV5SizeImage: bV5SizeImage.readUInt16LE(0),
    _bV5SizeImage: bV5SizeImage,
    bV5XPelsPerMeter: bV5XPelsPerMeter.readUInt16LE(0),
    _bV5XPelsPerMeter: bV5XPelsPerMeter,
    bV5YPelsPerMeter: bV5YPelsPerMeter.readUInt16LE(0),
    _bV5YPelsPerMeter: bV5YPelsPerMeter,
    bV5ClrUsed: bV5ClrUsed.readUInt16LE(0),
    _bV5ClrUsed: bV5ClrUsed,
    bV5ClrImportant: bV5ClrImportant.readUInt16LE(0),
    _bV5ClrImportant: bV5ClrImportant,
    bV5RedMask: bV5RedMask.readUInt16LE(0),
    _bV5RedMask: bV5RedMask,
    bV5GreenMask: bV5GreenMask.readUInt16LE(0),
    _bV5GreenMask: bV5GreenMask,
    bV5BlueMask: bV5BlueMask.readUInt16LE(0),
    _bV5BlueMask: bV5BlueMask,
    bV5AlphaMask: bV5AlphaMask.readUInt16LE(0),
    _bV5AlphaMask: bV5AlphaMask,
    bV5CSType: bV5CSType.readUInt16LE(0),
    _bV5CSType: bV5CSType,
    bV5Endpoints: null,
    _bV5Endpoints: bV5Endpoints,
    bV5GammaRed: bV5GammaRed.readUInt16LE(0),
    _bV5GammaRed: bV5GammaRed,
    bV5GammaGreen: bV5GammaGreen.readUInt16LE(0),
    _bV5GammaGreen: bV5GammaGreen,
    bV5GammaBlue: bV5GammaBlue.readUInt16LE(0),
    _bV5GammaBlue: bV5GammaBlue,
    bV5Intent: bV5Intent.readUInt16LE(0),
    _bV5Intent: bV5Intent,
    bV5ProfileData: bV5ProfileData.readUInt16LE(0),
    _bV5ProfileData: bV5ProfileData,
    bV5ProfileSize: bV5ProfileSize.readUInt16LE(0),
    _bV5ProfileSize: bV5ProfileSize,
    bV5Reserved: 0,
    _bV5Reserved: bV5Reserved
  };
};
Bitmap.prototype.readCoreHeaderOS2_V1 = function (){
  throw new Error('not yet impl');

  var bcWidth = this.read(this.buffer, 0x12, 2);
  var bcHeight = this.read(this.buffer, 0x14, 2);
  var bcPlanes = this.read(this.buffer, 0x16, 2);
  var bcBitCount = this.read(this.buffer, 0x18, 2);

  this.coreHeader = {
    __compression__: 0,
    __bitCount__: bcBitCount.readUInt8(0),
    __width__: bcWidth.readUInt8(0),
    __height__: bcHeight.readUInt8(0),
    bcWidth: bcWidth.readUInt8(0),
    _bcWidth: bcWidth,
    bcHeight: bcHeight.readUInt8(0),
    _bcHeight: bcHeight,
    bcPlanes: bcPlanes.readUInt8(0),
    _bcPlanes: bcPlanes,
    bcBitCount: bcBitCount.readUInt8(0),
    _bcBitCount: bcBitCount
  };
};
Bitmap.prototype.readCoreHeaderOS2_V2 = function (){
  throw new Error('not yet impl');

  var cx = this.read(this.buffer, 0x12, 4);
  var cy = this.read(this.buffer, 0x16, 4);
  var cPlanes = this.read(this.buffer, 0x1a, 2);
  var cBitCount = this.read(this.buffer, 0x1c, 2);
  var ulCompression = this.read(this.buffer, 0x1e, 4);
  var cbImage = this.read(this.buffer, 0x22, 4);
  var cxResolution = this.read(this.buffer, 0x26, 4);
  var cyResolution = this.read(this.buffer, 0x2a, 4);
  var cclrUsed = this.read(this.buffer, 0x2e, 4);
  var cclrImportant = this.read(this.buffer, 0x32, 4);
  var usUnits = this.read(this.buffer, 0x36, 2);
  var usReserved = this.read(this.buffer, 0x38, 2);
  var usRecording = this.read(this.buffer, 0x3a, 2);
  var usRendering = this.read(this.buffer, 0x3c, 2);
  var cSize1 = this.read(this.buffer, 0x3e, 4);
  var cSize2 = this.read(this.buffer, 0x42, 4);
  var ulColorEncoding = this.read(this.buffer, 0x46, 4);
  var ulIdentifier = this.read(this.buffer, 0x4a, 4);

  this.coreHeader = {
    __compression__: ulCompression.readUInt16LE(0),
    __bitCount__: cBitCount.readUInt8(0),
    __width__: cx.readUInt16LE(0),
    __height__: cy.readUInt16LE(0),
    cx: cx.readUInt16LE(0),
    _cx: cx,
    cy: cy.readUInt16LE(0),
    _cy: cy,
    cPlanes: cPlanes.readUInt8(0),
    _cPlanes: cPlanes,
    cBitCount: cBitCount.readUInt8(0),
    _cBitCount: cBitCount,
    ulCompression: ulCompression.readUInt16LE(0),
    _ulCompression: ulCompression,
    cbImage: cbImage.readUInt16LE(0),
    _cbImage: cbImage,
    cxResolution: cxResolution.readUInt16LE(0),
    _cxResolution: cxResolution,
    cyResolution: cyResolution.readUInt16LE(0),
    _cyResolution: cyResolution,
    cclrUsed: cclrUsed.readUInt16LE(0),
    _cclrUsed: cclrUsed,
    cclrImportant: cclrImportant.readUInt16LE(0),
    _cclrImportant: cclrImportant,
    usUnits: usUnits.readUInt8(0),
    _usUnits: usUnits,
    usReserved: usReserved.readUInt8(0),
    _usReserved: usReserved,
    usRecording: usRecording.readUInt8(0),
    _usRecording: usRecording,
    usRendering: usRendering.readUInt8(0),
    _usRendering: usRendering,
    cSize1: cSize1.readUInt16LE(0),
    _cSize1: cSize1,
    cSize2: cSize2.readUInt16LE(0),
    _cSize1: cSize1,
    ulColorEncoding: ulColorEncoding.readUInt16LE(0),
    _ulColorEncoding: ulColorEncoding,
    ulIdentifier: ulIdentifier.readUInt16LE(0),
    _ulIdentifier: ulIdentifier
  };
};
Bitmap.prototype.readColorPalette = function (){
  var bitCount = this.coreHeader.__bitCount__;
  if(this.BITCOUNT_16bit == bitCount){
    return /* nop */;
  }
  if(this.BITCOUNT_24bit == bitCount){
    return /* nop */;
  }
  if(this.BITCOUNT_32bit == bitCount){
    return /* nop */;
  }

  var coreType = this.infoHeader.readUInt16LE(0);
  switch(coreType){
  case this.BITMAPCOREHEADER:
    return this.readColorPalette_RGBTRIPLE(bitCount, 0x1a);
  case this.BITMAPINFOHEADER2:
    return this.readColorPalette_RGBTRIPLE(bitCount, 0x4e);
    case this.BITMAPV4HEADER:
    return this.readColorPalette_RGBQUAD(bitCount, 0x7a);
  case this.BITMAPV5HEADER:
    return this.readColorPalette_RGBQUAD(bitCount, 0x8a);
  case this.BITMAPINFOHEADER:
    return this.readColorPalette_RGBQUAD(bitCount, 0x36);
  default:
    throw new Error('unknown colorPalette: ' + coreType + ',' + bitCount);
  }
};
Bitmap.prototype.readColorPalette_RGBTRIPLE = function (bitCount, startPos){
  throw new Error('not yet impl');
};
Bitmap.prototype.readColorPalette_RGBQUAD = function (bitCount, startPos){
  if(this.BITCOUNT_2 == bitCount){
    return this.readRGBQUAD(1 << this.BITCOUNT_2, startPos);
  }
  if(this.BITCOUNT_16 == bitCount){
    return this.readRGBQUAD(1 << this.BITCOUNT_16, startPos);
  }
  if(this.BITCOUNT_256 == bitCount){
    return this.readRGBQUAD(1 << this.BITCOUNT_256, startPos);
  }
  throw new Error('unknown bitCount: ' + bitCount);
};
Bitmap.prototype.readRGBQUAD = function(count, startPos){
  var palette = [];
  for(var i = startPos, len = startPos + (4 * count); i < len; i += 4){
    palette.push({
      rgbBlue: this.read(this.buffer, i, 1).readUInt8(0),
      rgbGreen: this.read(this.buffer, i + 1, 1).readUInt8(0),
      rgbRed: this.read(this.buffer, i + 2, 1).readUInt8(0),
      rgbReserved: this.read(this.buffer, i + 3, 1).readUInt8(0)
    });
  }
  this.colorPalette = palette;
};
Bitmap.prototype.initDataPos = function(){
  var bitCount = this.coreHeader.__bitCount__;
  var hasPalette = true;
  if(this.BITCOUNT_16bit == bitCount){
    hasPalette = true;
  }
  if(this.BITCOUNT_24bit == bitCount){
    hasPalette = true;
  }
  if(this.BITCOUNT_32bit == bitCount){
    hasPalette = true;
  }

  var coreType = this.infoHeader.readUInt16LE(0);
  switch(coreType){
  case this.BITMAPCOREHEADER:
    this.dataPos = 0x1a;
    if(hasPalette){
      this.dataPos = this.dataPos + (3 * (1 << bitCount));
    }
    break;
  case this.BITMAPINFOHEADER2:
    this.dataPos = 0x4e;
    if(hasPalette){
      this.dataPos = this.dataPos + (3 * (1 << bitCount));
    }
    break;
  case this.BITMAPV4HEADER:
    this.dataPos = 0x7a;
    if(hasPalette){
      this.dataPos = this.dataPos + (4 * (1 << bitCount));
    }
    break;
  case this.BITMAPV5HEADER:
    this.dataPos = 0x8a;
    if(hasPalette){
      this.dataPos = this.dataPos + (4 * (1 << bitCount));
    }
  case this.BITMAPINFOHEADER:
    this.dataPos = 0x36;
    if(hasPalette){
      this.dataPos = this.dataPos + (4 * (1 << bitCount));
    }
    break;
  default:
    throw new Error('unknown colorPalette: ' + coreType + ',' + bitCount);
  }
};
Bitmap.prototype.mapRGBA = function(r, g, b, a){
  var hex = [];

  var padHex = function(value){
    var h = value.toString(16);
    if(value < 0x0f){
      return '0' + h;
    }
    return h;
  };

  hex.push(padHex(r));
  hex.push(padHex(g));
  hex.push(padHex(b));

  return '#' + hex.join('');
};
Bitmap.prototype.mapColor = function(bmpBuf, bitCount){
  var b, g, r, a;
  var length = bmpBuf.length;
  var colorData = [];

  if(this.BITCOUNT_2 == bitCount){
    for(var i = 0; i < length; ++i){
      var paletteValue = bmpBuf[i];
      var bin = paletteValue.toString(2);
      bin = new Array(8 - bin.length).join('0') + bin;

      for(var j = 0; j < bin.length; ++j){
        var paletteIndex = parseInt(bin.substring(j, j + 1), 10);
        var palette = this.colorPalette[paletteIndex];
        colorData.push(this.mapRGBA(palette.rgbRed, palette.rgbGreen, palette.rgbBlue, -1));
      }
    }
    return colorData;
  }
  if(this.BITCOUNT_16 == bitCount){
    for(var i = 0; i < length; i += 2){
      var paletteHigh = bmpBuf.readUInt8(i);
      var paletteLow = bmpBuf.readUInt8(i + 1);
      var indexes = [paletteHigh, paletteLow];
      indexes.forEach(function(paletteIndex){
        var palette = this.colorPalette[paletteIndex];
        colorData.push(this.mapRGBA(palette.rgbRed, palette.rgbGreen, palette.rgbBlue, -1));
      });
    }

    return colorData;
  }
  if(this.BITCOUNT_256 == bitCount){
    for(var i = 0; i < length; ++i){
      var paletteIndex = bmpBuf.readUInt16LE(i);
      var palette = this.colorPalette[paletteIndex];
      colorData.push(this.mapRGBA(palette.rgbRed, palette.rgbGreen, palette.rgbBlue, -1));
    }
    return colorData;
  }
  if(this.BITCOUNT_16bit == bitCount){
    for(var i = 0; i < length; i += 3){
      b = bmpBuf[i];
      g = bmpBuf[i + 1];
      r = bmpBuf[i + 2];
      colorData.push(this.mapRGBA(r, g, b, -1));
    }
    return colorData;
  }
  if(this.BITCOUNT_24bit == bitCount){
    for(var i = 0; i < length; i += 3){
      b = bmpBuf[i];
      g = bmpBuf[i + 1];
      r = bmpBuf[i + 2];
      colorData.push(this.mapRGBA(r, g, b, -1));
    }
    return colorData;
  }
  if(this.BITCOUNT_32bit == bitCount){
    for(var i = 0; i < length; i += 4){
      b = bmpBuf[i];
      g = bmpBuf[i + 1];
      r = bmpBuf[i + 2];
      a = bmpBuf[i + 3];
      colorData.push(this.mapRGBA(r, g, b, a));
    }
    return colorData;
  }
  throw new Error('unknown bitCount: ' + bitCount);
};
