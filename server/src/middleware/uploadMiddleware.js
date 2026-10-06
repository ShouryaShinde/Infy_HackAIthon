import multer from "multer";
import path from "path";
import fs from "fs";

// Ensure upload directory exists
const uploadDir = path.join(process.cwd(), "temp_uploads");
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
        const ext = path.extname(file.originalname) || ".mp4";
        cb(null, `${file.fieldname}-${uniqueSuffix}${ext}`);
    }
});

const fileFilter = (req, file, cb) => {
    // Allow common video and audio formats
    const allowedExtensions = /\.(mp4|mkv|mov|avi|webm|flv|wmv|mp3|wav|m4a|aac|ogg)$/i;
    const isExtAllowed = allowedExtensions.test(path.extname(file.originalname));

    if (isExtAllowed || file.mimetype.startsWith("video/") || file.mimetype.startsWith("audio/")) {
        cb(null, true);
    } else {
        cb(new Error("Only video (.mp4, .mkv, .mov, etc.) and audio files are supported!"), false);
    }
};

export const upload = multer({
    storage: storage,
    limits: {
        fileSize: 200 * 1024 * 1024 // 200MB limit
    },
    fileFilter: fileFilter
});
