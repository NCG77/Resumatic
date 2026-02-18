"use client";

import { useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { useAuth } from "@/context/AuthContext";
import styles from "./main_page.module.css";

interface Experience {
  title: string;
  company: string;
  bullets: string[];
}

interface Project {
  name: string;
  why_it_matters_for_this_job: string;
  bullets: string[];
}

interface ResumeStrategy {
  experience: Experience[];
  projects: Project[];
  skills_to_highlight: string[];
  skills_to_downplay: string[];
  keywords_for_ATS: string[];
  achievements: string[];
  overall_candidate_positioning: string;
  company_alignment_tips?: string[];
}

interface TailoredResult {
  jd_analysis: string;
  strategy: ResumeStrategy | string;
  strategy_raw: string;
  company_info: string | null;
  retrieved_context: string[];
}

export default function MainPage() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeFileName, setResumeFileName] = useState("");
  const [indexName, setIndexName] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<TailoredResult | null>(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [activeTab, setActiveTab] = useState<
    "strategy" | "analysis" | "context"
  >("strategy");
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
          job_url: jobUrl,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to tailor resume");
      }

      const data = await response.json();
      console.log("API Response:", data);

      if (data.error) {
        throw new Error(data.error);
      }

      setResult(data);
    } catch (err) {
      console.error("Error:", err);
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
          <label htmlFor="jobUrl">Job Posting URL (Optional)</label>
          <input
            id="jobUrl"
            type="url"
            value={jobUrl}
            onChange={(e) => setJobUrl(e.target.value)}
            placeholder="https://example.com/job-posting (for web scraping)"
            className={styles.input}
          />
        </div>
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
          {loading ? "Analyzing & Strategizing..." : "Generate Resume Strategy"}
        </button>
        {error && <div className={styles.error}>{error}</div>}
      </div>

      {result && (
        <div className={styles.resultSection}>
          <details
            style={{
              marginBottom: "20px",
              padding: "10px",
              background: "#f0f0f0",
              borderRadius: "8px",
            }}
          >
            <summary>Debug: Raw API Response</summary>
            <pre
              style={{ overflow: "auto", maxHeight: "200px", fontSize: "12px" }}
            >
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>

          {result.company_info && (
            <div className={styles.companyBadge}>
              Company Detected: <strong>{result.company_info}</strong>
            </div>
          )}

          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${activeTab === "strategy" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("strategy")}
            >
              Resume Strategy
            </button>
            <button
              className={`${styles.tab} ${activeTab === "analysis" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("analysis")}
            >
              JD Analysis
            </button>
            <button
              className={`${styles.tab} ${activeTab === "context" ? styles.activeTab : ""}`}
              onClick={() => setActiveTab("context")}
            >
              Retrieved Context
            </button>
          </div>

          {activeTab === "strategy" && (
            <div className={styles.strategySection}>
              {result.strategy &&
              typeof result.strategy === "object" &&
              result.strategy !== null ? (
                <>
                  <div className={styles.positioningCard}>
                    <h3>Candidate Positioning</h3>
                    <p>{result.strategy.overall_candidate_positioning}</p>
                  </div>

                  {result.strategy.experience?.length > 0 && (
                    <div className={styles.strategyCard}>
                      <h3>Experience</h3>
                      {result.strategy.experience.map((exp, idx) => (
                        <div key={idx} className={styles.experienceItem}>
                          <h4>
                            {exp.title} @ {exp.company}
                          </h4>
                          <ul>
                            {exp.bullets.map((bullet, bIdx) => (
                              <li key={bIdx}>{bullet}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}

                  {result.strategy.projects?.length > 0 && (
                    <div className={styles.strategyCard}>
                      <h3>Projects</h3>
                      {result.strategy.projects.map((proj, idx) => (
                        <div key={idx} className={styles.projectItem}>
                          <h4>{proj.name}</h4>
                          <p className={styles.projectReason}>
                            {proj.why_it_matters_for_this_job}
                          </p>
                          <ul>
                            {proj.bullets.map((bullet, bIdx) => (
                              <li key={bIdx}>{bullet}</li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className={styles.skillsGrid}>
                    <div className={styles.skillCard}>
                      <h3>Skills to Highlight</h3>
                      <div className={styles.tagList}>
                        {result.strategy.skills_to_highlight?.map(
                          (skill, idx) => (
                            <span key={idx} className={styles.highlightTag}>
                              {skill}
                            </span>
                          ),
                        )}
                      </div>
                    </div>
                    <div className={styles.skillCard}>
                      <h3>Skills to Downplay</h3>
                      <div className={styles.tagList}>
                        {result.strategy.skills_to_downplay?.map(
                          (skill, idx) => (
                            <span key={idx} className={styles.downplayTag}>
                              {skill}
                            </span>
                          ),
                        )}
                      </div>
                    </div>
                  </div>

                  <div className={styles.strategyCard}>
                    <h3>ATS Keywords</h3>
                    <div className={styles.tagList}>
                      {result.strategy.keywords_for_ATS?.map((keyword, idx) => (
                        <span key={idx} className={styles.atsTag}>
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>

                  {result.strategy.achievements?.length > 0 && (
                    <div className={styles.strategyCard}>
                      <h3>Achievements</h3>
                      <ul>
                        {result.strategy.achievements.map(
                          (achievement, idx) => (
                            <li key={idx}>{achievement}</li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}

                  {result.strategy.company_alignment_tips &&
                    result.strategy.company_alignment_tips.length > 0 && (
                      <div className={styles.strategyCard}>
                        <h3>Company Alignment Tips</h3>
                        <ul>
                          {result.strategy.company_alignment_tips.map(
                            (tip, idx) => (
                              <li key={idx}>{tip}</li>
                            ),
                          )}
                        </ul>
                      </div>
                    )}
                </>
              ) : (
                <div className={styles.rawStrategy}>
                  <ReactMarkdown>
                    {result.strategy_raw ||
                      (typeof result.strategy === "string"
                        ? result.strategy
                        : "No strategy generated")}
                  </ReactMarkdown>
                </div>
              )}
              <button
                className={styles.copyButton}
                onClick={() => {
                  navigator.clipboard.writeText(result.strategy_raw || "");
                  alert("Strategy copied to clipboard!");
                }}
              >
                Copy Strategy to Clipboard
              </button>
            </div>
          )}

          {activeTab === "analysis" && (
            <div className={styles.analysisSection}>
              <h3>Job Description Analysis</h3>
              <div className={styles.resumeContent}>
                <ReactMarkdown>{result.jd_analysis}</ReactMarkdown>
              </div>
            </div>
          )}

          {activeTab === "context" && result.retrieved_context?.length > 0 && (
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
