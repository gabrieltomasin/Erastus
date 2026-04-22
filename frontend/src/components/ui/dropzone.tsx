"use client";

import { useCallback, useState } from "react";
import { Upload, X } from "lucide-react";

const ACCEPTED_TYPES = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".zip"];
const ACCEPTED_MIME = "audio/mpeg,audio/wav,audio/mp4,audio/ogg,audio/flac,application/zip,application/x-zip-compressed";

interface DropzoneProps {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

export function Dropzone({ onFiles, disabled }: DropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files).filter((f) => {
        const ext = "." + f.name.split(".").pop()?.toLowerCase();
        return ACCEPTED_TYPES.includes(ext);
      });
      if (files.length > 0) {
        setSelectedFiles(files);
        onFiles(files);
      }
    },
    [onFiles]
  );

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) {
        setSelectedFiles(files);
        onFiles(files);
      }
    },
    [onFiles]
  );

  const clearFiles = () => {
    setSelectedFiles([]);
  };

  return (
    <div>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
          isDragging
            ? "border-primary bg-primary/10"
            : "border-border hover:border-muted-foreground"
        } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
      >
        <Upload className="h-8 w-8 text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground text-center">
          Arraste arquivos de áudio ou ZIP aqui
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          Suporta: {ACCEPTED_TYPES.join(", ")}
        </p>
        <label className="mt-3 cursor-pointer">
          <span className="inline-flex items-center gap-1 rounded-lg bg-muted px-3 py-1.5 text-sm font-medium hover:bg-border transition-colors">
            Selecionar arquivos
          </span>
          <input
            type="file"
            accept={ACCEPTED_MIME}
            multiple
            onChange={handleInput}
            className="hidden"
            disabled={disabled}
          />
        </label>
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-3 space-y-1">
          {selectedFiles.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-sm rounded-lg border border-border px-3 py-1.5">
              <span className="flex-1 truncate">{f.name}</span>
              <span className="text-muted-foreground text-xs">
                {(f.size / 1024 / 1024).toFixed(1)} MB
              </span>
              <button onClick={clearFiles} className="text-muted-foreground hover:text-destructive">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
