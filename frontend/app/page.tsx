
"use client";

import { useRef, useState } from "react";
import {
  Aperture,
  ArrowUpRight,
  Check,
  ChevronDown,
  Clapperboard,
  Clock3,
  CloudUpload,
  Download,
  Film,
  FolderOpen,
  Image as ImageIcon,
  Layers3,
  Loader2,
  Plus,
  Settings2,
  Sparkles,
  Upload,
  Video,
  WandSparkles,
  X,
} from "lucide-react";

export default function Home() {
  const videoInput = useRef<HTMLInputElement>(null);
  const imageInput = useRef<HTMLInputElement>(null);

  const [video, setVideo] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState("");
  const [duration, setDuration] = useState<number | null>(null);
  const [background, setBackground] = useState<File | null>(null);
  const [backgroundUrl, setBackgroundUrl] = useState("");
  const [quality, setQuality] = useState("1080p");
  const [uploadError, setUploadError] = useState("");

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remaining = Math.floor(seconds % 60);
    return `${minutes}:${String(remaining).padStart(2, "0")}`;
  };

  const handleVideo = (file?: File) => {
    if (!file) return;

    setUploadError("");

    if (!file.type.startsWith("video/")) {
      setUploadError("Please select a valid video file.");
      return;
    }

    const url = URL.createObjectURL(file);
    const media = document.createElement("video");

    media.preload = "metadata";
    media.onloadedmetadata = () => {
      URL.revokeObjectURL(url);

      if (!Number.isFinite(media.duration) || media.duration <= 0) {
        setUploadError("Unable to read video duration.");
        return;
      }

      if (media.duration > 360) {
        setUploadError("Video must be 6 minutes or shorter.");
        return;
      }

      setVideo(file);
      setDuration(media.duration);

      const previewUrl = URL.createObjectURL(file);
      setVideoUrl((old) => {
        if (old) URL.revokeObjectURL(old);
        return previewUrl;
      });
    };

    media.onerror = () => {
      URL.revokeObjectURL(url);
      setUploadError("Unable to read this video. Try another file.");
    };

    media.src = url;
  };

  const handleBackground = (file?: File) => {
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setUploadError("Please select a valid background image.");
      return;
    }

    const url = URL.createObjectURL(file);

    setBackgroundUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return url;
    });

    setBackground(file);
    setUploadError("");
  };

  const removeVideo = () => {
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideo(null);
    setVideoUrl("");
    setDuration(null);
    if (videoInput.current) videoInput.current.value = "";
  };

  const removeBackground = () => {
    if (backgroundUrl) URL.revokeObjectURL(backgroundUrl);
    setBackground(null);
    setBackgroundUrl("");
    if (imageInput.current) imageInput.current.value = "";
  };

  return (
    <main className="studio">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Aperture size={23} /></div>
          <div>
            <h2>Background<span>Studio</span></h2>
            <p>AI VIDEO EDITOR</p>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          <a className="nav-item active" href="#">
            <Layers3 size={18} /> Dashboard
          </a>
          <a className="nav-item" href="#editor">
            <Clapperboard size={18} /> New project
          </a>
          <a className="nav-item" href="#projects">
            <FolderOpen size={18} /> My projects
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="upgrade-card">
            <div className="upgrade-icon"><Sparkles size={19} /></div>
            <h3>AI-powered editing</h3>
            <p>Remove backgrounds and create something amazing.</p>
            <span>OPEN SOURCE AI <ArrowUpRight size={13} /></span>
          </div>
          <a className="nav-item settings-link" href="#settings">
            <Settings2 size={18} /> Settings
          </a>
          <div className="profile">
            <div className="avatar">O</div>
            <div>
              <strong>My Workspace</strong>
              <small>Personal account</small>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <section className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="slash">/</span>
            <strong>Dashboard</strong>
          </div>
          <div className="top-actions">
            <span className="engine-status">
              <span className="status-dot" /> AI ENGINE READY
            </span>
            <button className="icon-button" aria-label="Settings">
              <Settings2 size={19} />
            </button>
          </div>
        </header>

        <div className="content">
          <section className="welcome-section">
            <div>
              <div className="eyebrow"><Sparkles size={14} /> YOUR CREATIVE WORKSPACE</div>
              <h1>Make your videos <span>stand out.</span></h1>
              <p>Remove any video background with AI and replace it with your own creative vision.</p>
            </div>
            <div className="welcome-decoration"><WandSparkles size={65} /></div>
          </section>

          <div className="section-heading" id="editor">
            <div>
              <h2>Create a new project</h2>
              <p>Start with a video, then choose your perfect background.</p>
            </div>
            <span className="duration-limit"><Clock3 size={14} /> MAX 06:00 MIN</span>
          </div>

          <div className="editor-grid">
            <div className="editor-main">
              <div className="panel upload-panel">
                <div className="panel-heading">
                  <div className="step-number">01</div>
                  <div>
                    <h3>Import your video</h3>
                    <p>Upload the video you want to edit.</p>
                  </div>
                  {video && <span className="complete-label"><Check size={13} /> ADDED</span>}
                </div>

                {!video ? (
                  <button
                    className="drop-zone"
                    onClick={() => videoInput.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleVideo(e.dataTransfer.files[0]);
                    }}
                  >
                    <div className="upload-icon"><CloudUpload size={28} /></div>
                    <strong>Drop your video here</strong>
                    <span>or <b>browse files</b> from your device</span>
                    <div className="file-types">
                      <span>MP4</span><span>MOV</span><span>WEBM</span>
                      <i>UP TO 6 MINUTES</i>
                    </div>
                  </button>
                ) : (
                  <div className="file-card">
                    <div className="file-icon"><Video size={23} /></div>
                    <div className="file-info">
                      <strong>{video.name}</strong>
                      <span>{(video.size / (1024 * 1024)).toFixed(1)} MB · {duration !== null ? formatTime(duration) : "Reading..."}</span>
                    </div>
                    <button className="remove-button" onClick={removeVideo} aria-label="Remove video"><X size={17} /></button>
                  </div>
                )}

                <input
                  ref={videoInput}
                  type="file"
                  accept="video/*"
                  hidden
                  onChange={(e) => handleVideo(e.target.files?.[0])}
                />
              </div>

              <div className="panel preview-panel">
                <div className="panel-heading">
                  <div className="step-number">02</div>
                  <div>
                    <h3>Video preview</h3>
                    <p>Preview your imported video.</p>
                  </div>
                  <span className="preview-tag">LIVE PREVIEW</span>
                </div>

                <div className="preview-stage">
                  {videoUrl ? (
                    <video
                      src={videoUrl}
                      controls
                      playsInline
                      className="video-preview"
                    />
                  ) : (
                    <div className="empty-preview">
                      <div className="empty-preview-icon"><Film size={34} /></div>
                      <strong>Your video will appear here</strong>
                      <span>Import a video to get started</span>
                    </div>
                  )}
                </div>

                <div className="preview-footer">
                  <span><span className="status-dot" /> {video ? "ORIGINAL VIDEO" : "WAITING FOR VIDEO"}</span>
                  <span>{duration !== null ? formatTime(duration) : "00:00"}</span>
                </div>
              </div>

              <div className="panel background-panel">
                <div className="panel-heading">
                  <div className="step-number">03</div>
                  <div>
                    <h3>Choose your background</h3>
                    <p>Upload an image to use as your new background.</p>
                  </div>
                </div>

                <div className="background-content">
                  <button
                    className="background-upload"
                    onClick={() => imageInput.current?.click()}
                  >
                    {backgroundUrl ? (
                      <img src={backgroundUrl} alt="Selected background" />
                    ) : (
                      <>
                        <div className="background-upload-icon"><ImageIcon size={22} /></div>
                        <strong>Upload background</strong>
                        <span>JPG, PNG, WEBP</span>
                      </>
                    )}
                  </button>
                  <input
                    ref={imageInput}
                    type="file"
                    accept="image/*"
                    hidden
                    onChange={(e) => handleBackground(e.target.files?.[0])}
                  />
                  <div className="background-details">
                    <strong>{background ? background.name : "Your custom background"}</strong>
                    <p>{background ? "Image selected successfully." : "Choose any image from your device."}</p>
                    {background && (
                      <button className="text-button" onClick={removeBackground}>Remove image <X size={13} /></button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <aside className="editor-side">
              <div className="panel ai-panel">
                <div className="side-panel-title">
                  <div className="ai-symbol"><WandSparkles size={19} /></div>
                  <div><h3>AI Processing</h3><span>BACKGROUND REMOVAL</span></div>
                </div>
                <div className="ai-status">
                  <span className="status-dot muted" />
                  <span>Waiting for video</span>
                </div>
                <p className="ai-description">Our AI model will identify the person and separate them from the original background.</p>
                <div className="feature-list">
                  <div><Check size={15} /> Person segmentation</div>
                  <div><Check size={15} /> Fine edge matting</div>
                  <div><Check size={15} /> Frame consistency</div>
                </div>
                <div className="model-info">
                  <span>AI MODEL</span>
                  <strong>Robust Video Matting</strong>
                  <small>OPEN SOURCE · RVM</small>
                </div>
              </div>

              <div className="panel export-panel" id="settings">
                <div className="panel-heading compact">
                  <div className="export-icon"><Download size={18} /></div>
                  <div><h3>Export settings</h3><p>Configure your final video.</p></div>
                </div>

                <label className="field-label" htmlFor="quality">OUTPUT RESOLUTION</label>
                <select id="quality" value={quality} onChange={(e) => setQuality(e.target.value)}>
                  <option value="720p">HD · 720p</option>
                  <option value="1080p">Full HD · 1080p</option>
                  <option value="1440p">QHD · 1440p</option>
                  <option value="2160p">4K · 2160p</option>
                </select>

                <div className="export-format">
                  <span>FORMAT</span>
                  <strong>MP4 (H.264)</strong>
                </div>

                <button
                  className="export-button"
                  disabled={!video || !background}
                  onClick={() => alert("AI processing and export will be enabled after backend integration.")}
                >
                  <Sparkles size={17} /> Export video <ArrowUpRight size={16} />
                </button>
                <p className="export-note">AI processing and export will be available after backend integration.</p>
              </div>

              <div className="tip-card">
                <Sparkles size={17} />
                <div>
                  <strong>Pro tip</strong>
                  <p>Use a high-quality background image with a similar lighting direction for a more realistic result.</p>
                </div>
              </div>
            </aside>
          </div>

          {uploadError && (
            <div className="error-message">
              <X size={16} /> {uploadError}
            </div>
          )}

          <section className="projects-section" id="projects">
            <div className="projects-heading">
              <div><h2>Recent projects</h2><p>Your video editing workspace.</p></div>
              <span>0 PROJECTS</span>
            </div>
            <div className="empty-projects">
              <div><FolderOpen size={25} /></div>
              <strong>No projects yet</strong>
              <span>Your completed projects will appear here.</span>
            </div>
          </section>

          <footer className="footer">
            <span>BACKGROUND STUDIO <span className="footer-dot">●</span> AI VIDEO EDITOR</span>
            <span>BUILT WITH OPEN SOURCE AI <Sparkles size={12} /></span>
          </footer>
        </div>
      </section>
    </main>
  );
}
