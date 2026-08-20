OUTPUT_BANDS = [
    "rojo", "verde", "azul", "ndci", "clorofila", "fai", "ndvi", "ndwi", "agua", "mascara",
    "b05", "b07", "b08", "b8a", "b11", "b12", "clm", "clp",
]

EVALSCRIPT_CIANOBACTERIA = """
//VERSION=3
function setup() {
  return {
    input: [{
      bands: ["B02", "B03", "B04", "B05", "B07", "B08", "B8A", "B11", "B12", "dataMask", "CLM", "CLP"],
      units: ["REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE",
              "REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "REFLECTANCE", "DN", "DN", "DN"]
    }],
    output: { bands: 18, sampleType: "FLOAT32" }
  };
}

function evaluatePixel(s) {
  let r = s.B04;
  let g = s.B03;
  let b = s.B02;
  let nir = s.B08;
  let swir1 = s.B11;
  let swir2 = s.B12;

  let ndvi = (nir - r) / (nir + r);
  let mndwi = (g - swir1) / (g + swir1);
  let ndwi = (g - nir) / (g + nir);
  let ndwiLeaves = (nir - swir1) / (nir + swir1);
  let aweish = b + 2.5 * g - 1.5 * (nir + swir1) - 0.25 * swir2;
  let aweinsh = 4 * (g - swir1) - (0.25 * nir + 2.75 * swir1);
  let dbsi = ((swir1 - g) / (swir1 + g)) - ndvi;

  let agua = 0;
  if (mndwi > 0.42 || ndwi > 0.4 || aweinsh > 0.1879 || aweish > 0.1112 || ndvi < -0.2 || ndwiLeaves > 1) {
    agua = 1;
  }
  if (agua == 1 && (aweinsh <= -0.03 || dbsi > 0)) {
    agua = 0;
  }

  let fai = s.B07 - s.B04 - (s.B8A - s.B04) * (783 - 665) / (865 - 665);
  let ndci = (s.B05 - s.B04) / (s.B05 + s.B04);
  let clorofila = 826.57 * Math.pow(ndci, 3) - 176.43 * Math.pow(ndci, 2) + 19 * ndci + 4.071;

  return [
    s.B04, s.B03, s.B02, ndci, clorofila, fai, ndvi, ndwi, agua, s.dataMask,
    s.B05, s.B07, s.B08, s.B8A, s.B11, s.B12, s.CLM, s.CLP,
  ];
}
"""
