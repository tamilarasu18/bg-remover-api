<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/AI%20Powered-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" alt="AI Powered"/>
</p>

<h1 align="center">🎨 Background Remover API</h1>

<p align="center">
  <strong>AI-powered background removal service built with FastAPI and rembg</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## ✨ Features

| Feature                    | Description                                                      |
| -------------------------- | ---------------------------------------------------------------- |
| 🚀 **High Performance**    | Async processing with ThreadPoolExecutor for CPU-intensive tasks |
| 🎯 **Multiple Formats**    | Supports PNG (lossless) and WEBP (compressed) output             |
| 📡 **Dual Response Modes** | Stream binary images or get Base64 encoded JSON responses        |
| 🔒 **Production Ready**    | CORS configured, health probes, comprehensive error handling     |
| 📊 **Detailed Metrics**    | Processing time, compression ratio, and file size tracking       |
| 🐳 **Cloud Ready**         | Optimized for Azure Container Apps, AWS, and Docker deployments  |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/tamilarasu18/bg-remover-api.git
cd bg-remover-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

🌐 Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation

## 📚 API Reference

### Health Check

```http
GET /health
```

<details>
<summary>📋 Response Example</summary>

```json
{
  "status": "healthy",
  "message": "All services are operational - Ready to process images",
  "version": "1.0.1"
}
```

</details>

---

### Remove Background (Stream)

```http
POST /remove-background
Content-Type: multipart/form-data
```

| Parameter       | Type      | Default    | Description                       |
| --------------- | --------- | ---------- | --------------------------------- |
| `file`          | `file`    | _required_ | Image file (PNG, JPG, JPEG, WEBP) |
| `output_format` | `string`  | `PNG`      | Output format: `PNG` or `WEBP`    |
| `quality`       | `integer` | `95`       | WEBP quality (1-100)              |

**Returns:** Binary image stream with transparent background

<details>
<summary>📋 cURL Example</summary>

```bash
curl -X POST "http://localhost:8000/remove-background" \
  -F "file=@photo.jpg" \
  -F "output_format=PNG" \
  --output result.png
```

</details>

---

### Remove Background (Base64)

```http
POST /remove-background-base64
Content-Type: multipart/form-data
```

| Parameter       | Type      | Default    | Description                       |
| --------------- | --------- | ---------- | --------------------------------- |
| `file`          | `file`    | _required_ | Image file (PNG, JPG, JPEG, WEBP) |
| `output_format` | `string`  | `PNG`      | Output format: `PNG` or `WEBP`    |
| `quality`       | `integer` | `95`       | WEBP quality (1-100)              |

<details>
<summary>📋 Response Example</summary>

```json
{
  "success": true,
  "message": "Background removed successfully from photo.jpg",
  "base64_image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "processing_time": 1.23,
  "output_format": "png",
  "original_size": 245678,
  "output_size": 198432,
  "compression_ratio": 19.23
}
```

</details>

## 🏗️ Architecture

```
bg-remover-api/
├── app/
│   ├── main.py          # FastAPI application & endpoints
│   ├── models.py        # Pydantic response models
│   └── utils.py         # Image validation & processing utilities
├── requirements.txt     # Python dependencies
└── README.md
```

### Tech Stack

- **Framework:** FastAPI with async/await support
- **AI Model:** rembg with U2-Net for precise segmentation
- **Image Processing:** Pillow for format conversion & optimization
- **Concurrency:** ThreadPoolExecutor for non-blocking CPU tasks

## 🐳 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t bg-remover-api .
docker run -p 8000:8000 bg-remover-api
```

### Azure Container Apps

The API includes built-in health probes at `/health` for container orchestration platforms.

## 📈 Performance

- **Model:** U2-Net (optimized for accuracy)
- **Avg Processing Time:** ~1-3 seconds per image
- **Max Workers:** 4 concurrent processing threads
- **Supported Image Size:** Up to 20MB

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/tamilarasu18">Tamilarasu M</a>
</p>
