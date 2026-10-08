// node lift.cjs in.jpg out.jpg [gamma=2.6] [gain=1.15] [offset=-10]  - lift the shadows of a photo strip
const sharp = require('sharp');
(async () => {
  const [src, out, g = '2.6', a = '1.15', b = '-10'] = process.argv.slice(2);
  await sharp(src).gamma(+g).linear(+a, +b).jpeg({ quality: 92 }).toFile(out);
  console.log(out);
})();
