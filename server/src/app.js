import express from "express";
import cors from "cors";
import summaryRoutes from "./routes/summaryRoutes.js"

const app = express();

// Middleware
app.use(cors({
    origin: process.env.CLIENT_URL,
    credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use("/api", summaryRoutes);

// Routes
app.get("/", (req, res) => {
    res.json({
        message: "API is running",
    });
});

export default app;