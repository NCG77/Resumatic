"use client";

import { useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { useAuth } from "@/context/AuthContext";
import styles from "./main_page.module.css";

interface TailoredResult {
  tailored_resume: string;
  suggestions: string[];
  match_score: number;
  retrieved_context: string[];
}

export default function MainPage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeFileName, setResumeFileName] = useState("");
  const [indexName, setIndexName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<TailoredResult | null>(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const { user, loading: authLoading, logout } = useAuth();

  const handleUploadResume = async () => {
    if (!resumeFile) {
      setError("Please select a file to upload");
      return;
    }

    setUploading(true);
    setError("");
    setSuccessMessage("");

    try {
      const formData = new FormData();
      formData.append("file", resumeFile);

      const response = await fetch("/api/upload-resume", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload resume");
      }

      const data = await response.json();
      setSuccessMessage(`Resume uploaded successfully! (${data.message})`);
      setResumeFileName(resumeFile.name);
      setIndexName(data.index_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload resume");
    } finally {
      setUploading(false);
    }
  };

  const handleTailorResume = async () => {
    if (!indexName || !jobDescription.trim()) {
      setError("Please upload a resume and fill in the job description");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/tailor-resume", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jd: jobDescription,
          index_name: indexName,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to tailor resume");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        {authLoading ? (
          <div className={styles.authLoading}>Loading...</div>
        ) : user ? (
          <div className={styles.userInfo}>
            <span className={styles.userEmail}>{user.email}</span>
            <button onClick={logout} className={styles.logoutButton}>
              Logout
            </button>
          </div>
        ) : (
          <div className={styles.authLinks}>
            <Link href="/login" className={styles.authLink}>
              Login
            </Link>
            <Link href="/signup" className={styles.authLinkPrimary}>
              Sign Up
            </Link>
          </div>
        )}
      </header>

      <h1>Resumatic</h1>
      <p className={styles.subtitle}>
        Tailor your resume to match the job description
      </p>

      <div className={styles.inputSection}>
        <div className={styles.resumeRowContainer}>
          <div className={styles.resumeLeft}>
            <label>Your Resume/Details File</label>
            <p className={styles.helpText}>
              Upload a file with all your projects, experience, certificates,
              achivements and details (TXT or PDF)
            </p>
            <p className={styles.helpText}>
              How it works:
              <br></br>
              1) File is uploaded and is split into chunks.
              <br></br>
              2) Those chunks are embedded and stored in a vector database.
              <br></br>
              3) Job discription is then read and embedded.
              <br></br>
              4) Jobdiscription embedding is used to retrieve relevant chunks
              from the vector database.
              <br></br>
              5) Those chunks are passed to a model for generating user
              experience data.
              <br></br>
              6) The experience data is passed to a 2nd model to tailored resume
              points to the job description and presented to the user.
            </p>
          </div>
          <div className={styles.resumeRight}>
            <div className={styles.uploadArea}>
              <input
                id="resume-file"
                type="file"
                accept=".txt,.pdf"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setResumeFile(file);
                    setError("");
                  }
                }}
                className={styles.fileInput}
              />
              <label htmlFor="resume-file" className={styles.uploadLabel}>
                <div className={styles.uploadContent}>
                  <span className={styles.uploadIcon}>📄</span>
                  <span className={styles.uploadText}>
                    {resumeFile
                      ? resumeFile.name
                      : "Click to upload or drag file here"}
                  </span>
                  <span className={styles.uploadHint}>(TXT or PDF)</span>
                </div>
              </label>
            </div>
            <button
              onClick={handleUploadResume}
              disabled={!resumeFile || uploading}
              className={styles.uploadButton}
            >
              {uploading ? "Uploading..." : "Upload File"}
            </button>
            {error && <div className={styles.error}>{error}</div>}
            {successMessage && (
              <div className={styles.success}>{successMessage}</div>
            )}
            {resumeFileName && (
              <div className={styles.uploadedInfo}>
                ✓ Active File: <strong>{resumeFileName}</strong>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className={styles.inputSection}>
        <div className={styles.formGroup}>
          <label htmlFor="jobDescription">Job Description</label>
          <textarea
            id="jobDescription"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the job description here..."
            className={styles.textarea}
            rows={10}
          />
        </div>
        <button
          onClick={handleTailorResume}
          disabled={loading}
          className={styles.button}
        >
          {loading ? "Tailoring Resume..." : "Tailor Resume"}
        </button>
      </div>

      {result && (
        <div className={styles.resultSection}>
          <div className={styles.suggestions}>
            <h3>Suggestions</h3>
            <ul>
              {result.suggestions.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </div>

          <div className={styles.tailoredResume}>
            <h3>Tailored Resume Points</h3>
            <div className={styles.resumeContent}>
              <ReactMarkdown>{result.tailored_resume}</ReactMarkdown>
            </div>
            <button
              className={styles.copyButton}
              onClick={() => {
                navigator.clipboard.writeText(result.tailored_resume);
                alert("Resume copied to clipboard!");
              }}
            >
              Copy to Clipboard
            </button>
          </div>

          {result.retrieved_context && result.retrieved_context.length > 0 && (
            <div className={styles.retrievedContext}>
              <h3>Retrieved from Your Database</h3>
              <div className={styles.contextList}>
                {result.retrieved_context.map((context, index) => (
                  <div key={index} className={styles.contextItem}>
                    {context}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
