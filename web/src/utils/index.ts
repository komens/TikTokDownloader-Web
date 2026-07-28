import type { WorkData, FileAccessInfo } from "@/types";

/**
 * 从路径中提取相对于 Volume 的相对路径
 * 兼容绝对路径，提取 Download/ 或 Temp/ 及之后的部分
 * 例如: /xxx/Volume/Download/文件.jpg -> Download/文件.jpg
 */
function extractRelativePath(pathStr: string): string {
  if (!pathStr) return "";
  if (!pathStr.includes("Volume")) return pathStr;
  const normalized = pathStr.replace(/\\/g, "/");
  const match = normalized.match(/(?:^|\/)(Download|Temp)\/(.+)$/);
  if (match) return `${match[1]}/${match[2]}`;
  return normalized;
}

/**
 * 对相对路径进行 URL 编码（保留 / 分隔符）
 * 必须编码 #、空格、中文等特殊字符，否则浏览器会把 # 之后当作 fragment 截断
 */
function encodePath(relativePath: string): string {
  if (!relativePath) return "";
  const normalized = relativePath.replace(/\\/g, "/");
  // 按 / 分割，逐段编码，再拼接，避免 / 被编码
  return normalized
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
}

export function getFileAccessInfoList(work: WorkData): FileAccessInfo[] {
  if (work.文件访问信息 && work.文件访问信息.length > 0) {
    // 兼容后端返回的 relative_path 可能是绝对路径的情况
    return work.文件访问信息.map((info) => {
      const relativePath = extractRelativePath(info.relative_path);
      return {
        ...info,
        relative_path: relativePath,
        url: info.url || `/files/${encodePath(relativePath)}`,
      };
    });
  }

  if (work.下载文件路径 && work.下载文件路径.length > 0) {
    return work.下载文件路径.map((fullPath) => {
      const relativePath = extractRelativePath(fullPath);
      const url = `/files/${encodePath(relativePath)}`;
      const filename = relativePath.split("/").pop() || fullPath.split("/").pop() || "";
      return {
        absolute_path: fullPath,
        relative_path: relativePath,
        url,
        filename,
      };
    });
  }

  return [];
}

export function getThumbnailUrl(work: WorkData): string {
  const fileList = getFileAccessInfoList(work);
  if (fileList.length === 0) return "";

  if (isVideoType(work)) {
    // 视频类型：优先使用后端返回的 thumbnail_url；否则从文件名构造 Temp 目录下的 jpg
    if (fileList[0]?.thumbnail_url) return fileList[0].thumbnail_url;
    const relativePath = fileList[0]?.relative_path || "";
    if (!relativePath) return "";
    const filename = relativePath.split("/").pop() || "";
    const stem = filename.replace(/\.[^.]+$/, "");
    return `/files/Temp/${encodeURIComponent(stem)}.jpg`;
  }
  // 图片类型：取第一张图片作为缩略图（复用 getMediaUrl 的路径处理逻辑）
  return getMediaUrl(work, 0);
}

export function getMediaUrl(work: WorkData, index: number): string {
  const fileList = getFileAccessInfoList(work);
  const fileInfo = fileList[index];
  if (!fileInfo) return "";

  // 优先使用后端返回的 url（已编码）
  if (fileInfo.url) return fileInfo.url;

  // 回退：从 relative_path 构造 URL（需编码）
  const relativePath = fileInfo.relative_path;
  if (relativePath) {
    return `/files/${encodePath(relativePath)}`;
  }

  return "";
}

export function getMediaCount(work: WorkData): number {
  const fileList = getFileAccessInfoList(work);
  return fileList.length;
}

export function isVideoType(work: WorkData | null | undefined): boolean {
  return work?.作品类型 === "视频";
}

export function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const parts = dateStr.split("_");
  if (parts.length >= 2) {
    return `${parts[0]} ${parts[1]}`;
  }
  return dateStr;
}

export function formatShortDate(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const parts = dateStr.split("_");
  if (parts.length >= 1) {
    return parts[0].slice(5);
  }
  return dateStr;
}

export function getTags(work: WorkData | null | undefined): string[] {
  if (!work?.作品标签) return [];
  if (Array.isArray(work.作品标签)) return work.作品标签;
  try {
    return JSON.parse(work.作品标签) as string[];
  } catch (error) {
    return work.作品标签.split(" ").filter((tag) => tag.trim());
  }
}

export function formatTime(dateStr: string | undefined): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
