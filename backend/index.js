import express from 'express';
import cors from "cors";
import dotenv from "dotenv";
import router from './src/routes/user.route.js';
dotenv.config();

const app = express();

// Middlewares
app.use(cors());
app.use(express.json());



// Example route
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", time: new Date().toISOString() });
});

app.use('/api', router);

// Pick port from environment (Docker injects PORT)
const port = process.env.PORT || 5000;

app.listen(port, () => {
  console.log(`🚀 Backend server running inside Docker on port ${port}`);
});
