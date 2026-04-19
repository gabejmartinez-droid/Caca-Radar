const MAX_LONGEST_SIDE = 1400;
const TARGET_MAX_BYTES = 500 * 1024;
const MIN_QUALITY = 0.45;
const INITIAL_QUALITY = 0.82;
const QUALITY_STEP = 0.08;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function supportsCanvasType(type) {
  const canvas = document.createElement("canvas");
  return canvas.toDataURL(type).startsWith(`data:${type}`);
}

async function readImageBitmap(file) {
  if (typeof createImageBitmap === "function") {
    try {
      return await createImageBitmap(file, { imageOrientation: "from-image" });
    } catch {
      return await createImageBitmap(file);
    }
  }

  const objectUrl = URL.createObjectURL(file);
  try {
    const image = await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("image-load-failed"));
      img.src = objectUrl;
    });
    return image;
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

function getScaledSize(width, height) {
  const longestSide = Math.max(width, height);
  if (longestSide <= MAX_LONGEST_SIDE) {
    return { width, height };
  }

  const scale = MAX_LONGEST_SIDE / longestSide;
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error("blob-generation-failed"));
      },
      type,
      quality
    );
  });
}

function getSquareCrop(width, height) {
  const size = Math.min(width, height);
  return {
    size,
    sx: Math.max(0, Math.round((width - size) / 2)),
    sy: Math.max(0, Math.round((height - size) / 2)),
  };
}

export async function compressReportPhoto(file) {
  if (!(file instanceof File) || !file.type.startsWith("image/")) {
    throw new Error("unsupported-file");
  }

  const image = await readImageBitmap(file);
  const sourceWidth = image.naturalWidth || image.videoWidth || image.width;
  const sourceHeight = image.naturalHeight || image.videoHeight || image.height;
  const { size, sx, sy } = getSquareCrop(sourceWidth, sourceHeight);
  const { width, height } = getScaledSize(size, size);

  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d", { alpha: false });
  if (!context) {
    throw new Error("canvas-not-supported");
  }

  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, width, height);
  context.drawImage(image, sx, sy, size, size, 0, 0, width, height);

  const preferredType = supportsCanvasType("image/webp") ? "image/webp" : "image/jpeg";
  const extension = preferredType === "image/webp" ? "webp" : "jpg";
  const baseName = (file.name || "report-photo").replace(/\.[^.]+$/, "");

  let quality = INITIAL_QUALITY;
  let candidate = await canvasToBlob(canvas, preferredType, quality);

  while (candidate.size > TARGET_MAX_BYTES && quality > MIN_QUALITY) {
    quality = clamp(Number((quality - QUALITY_STEP).toFixed(2)), MIN_QUALITY, INITIAL_QUALITY);
    candidate = await canvasToBlob(canvas, preferredType, quality);
    if (quality === MIN_QUALITY) {
      break;
    }
  }

  return new File([candidate], `${baseName}.${extension}`, {
    type: candidate.type || preferredType,
    lastModified: Date.now(),
  });
}

export const REPORT_PHOTO_MAX_BYTES = TARGET_MAX_BYTES;
