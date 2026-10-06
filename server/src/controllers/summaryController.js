import fs from "fs";
import { generateSummary, summarizeVideo, transcribeVideo } from "../services/aiService.js";

/**
 * Summarize raw text
 */
export const summarizeText = async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.status(400).json({
                success: false,
                message: "Text is required"
            });
        }

        const result = await generateSummary(text);

        return res.status(200).json({
            success: true,
            data: result.data
        });
    } catch (error) {
        console.error(
            "Summary Controller Error:",
            error.response?.data || error.message
        );

        return res.status(500).json({
            success: false,
            message: error.response?.data?.message || "Failed to generate summary",
            error: error.response?.data?.error || error.message
        });
    }
};

/**
 * Handle uploaded video file (.mp4, etc.), transcribe it and generate summary
 */
export const summarizeVideoFile = async (req, res) => {
    const uploadedFilePath = req.file?.path;

    try {
        if (!req.file) {
            return res.status(400).json({
                success: false,
                message: "Video file is required. Please upload with field name 'file' or 'video'."
            });
        }

        console.log(`[SummaryController] Received video upload: ${req.file.originalname} (${(req.file.size / (1024 * 1024)).toFixed(2)} MB)`);

        const result = await summarizeVideo(uploadedFilePath, req.file.originalname);

        return res.status(200).json({
            success: true,
            data: result.data
        });
    } catch (error) {
        console.error(
            "Video Summary Controller Error:",
            error.response?.data || error.message
        );

        return res.status(500).json({
            success: false,
            message: error.response?.data?.message || "Failed to transcribe and summarize video",
            error: error.response?.data?.error || error.message
        });
    } finally {
        // Clean up temporary uploaded file from Node server
        if (uploadedFilePath && fs.existsSync(uploadedFilePath)) {
            fs.unlink(uploadedFilePath, (err) => {
                if (err) console.error("Error removing temp upload file:", err);
            });
        }
    }
};

/**
 * Transcribe uploaded video/audio without summarizing
 */
export const transcribeVideoFile = async (req, res) => {
    const uploadedFilePath = req.file?.path;

    try {
        if (!req.file) {
            return res.status(400).json({
                success: false,
                message: "File is required. Please upload with field name 'file'."
            });
        }

        console.log(`[SummaryController] Received transcribe request: ${req.file.originalname}`);

        const result = await transcribeVideo(uploadedFilePath, req.file.originalname);

        return res.status(200).json({
            success: true,
            data: result.data
        });
    } catch (error) {
        console.error(
            "Transcription Controller Error:",
            error.response?.data || error.message
        );

        return res.status(500).json({
            success: false,
            message: error.response?.data?.message || "Failed to transcribe video",
            error: error.response?.data?.error || error.message
        });
    } finally {
        // Clean up temporary uploaded file
        if (uploadedFilePath && fs.existsSync(uploadedFilePath)) {
            fs.unlink(uploadedFilePath, (err) => {
                if (err) console.error("Error removing temp upload file:", err);
            });
        }
    }
};