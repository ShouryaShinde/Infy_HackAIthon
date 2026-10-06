import axios from "axios";
import FormData from "form-data";
import fs from "fs";

const AI_SERVICE_URL =
    process.env.AI_SERVICE_URL || "http://localhost:5000";

/**
 * Send raw text to AI Service for summarization
 */
export const generateSummary = async (text) => {
    const response = await axios.post(
        `${AI_SERVICE_URL}/summarize`,
        {
            text
        }
    );

    return response.data;
};

/**
 * Upload video/audio file to AI Service to transcribe
 */
export const transcribeVideo = async (filePath, originalFilename = "video.mp4") => {
    const formData = new FormData();
    formData.append("file", fs.createReadStream(filePath), {
        filename: originalFilename
    });

    const response = await axios.post(
        `${AI_SERVICE_URL}/transcribe`,
        formData,
        {
            headers: {
                ...formData.getHeaders()
            },
            maxContentLength: Infinity,
            maxBodyLength: Infinity,
            timeout: 300000 // 5-minute timeout for transcription
        }
    );

    return response.data;
};

/**
 * Upload video/audio file to AI Service to transcribe and summarize directly
 */
export const summarizeVideo = async (filePath, originalFilename = "video.mp4") => {
    const formData = new FormData();
    formData.append("file", fs.createReadStream(filePath), {
        filename: originalFilename
    });

    const response = await axios.post(
        `${AI_SERVICE_URL}/summarize-video`,
        formData,
        {
            headers: {
                ...formData.getHeaders()
            },
            maxContentLength: Infinity,
            maxBodyLength: Infinity,
            timeout: 300000 // 5-minute timeout for transcription + summarization
        }
    );

    return response.data;
};