import express from "express";
import { summarizeText, summarizeVideoFile, transcribeVideoFile } from "../controllers/summaryController.js";
import { upload } from "../middleware/uploadMiddleware.js";

const router = express.Router();

// POST /api/summarize (Text input)
router.post("/summarize", summarizeText);

// POST /api/summarize-video (Video/Audio upload .mp4 -> transcribe -> summary)
router.post("/summarize-video", upload.single("file"), summarizeVideoFile);

// POST /api/transcribe (Video/Audio upload .mp4 -> transcript only)
router.post("/transcribe", upload.single("file"), transcribeVideoFile);

export default router;