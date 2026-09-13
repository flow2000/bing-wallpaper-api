/*
 * Bing Wallpaper API - Netlify Functions 入口
 *
 * 功能说明：
 * 本文件是部署在 Netlify 上的无服务器函数，提供必应壁纸的查询接口。
 * 由于 Netlify Functions 仅支持 JS/TS/Go 运行时，因此使用 JavaScript 实现。
 *
 * 数据来源：
 * - /today 接口：实时请求必应官方接口，返回最新壁纸
 * - /random、/all、/total 接口：读取项目中 data/<mkt>_all.json 本地数据文件
 *   （由 GitHub Actions 每日自动更新并提交到仓库）
 *
 * 路由列表：
 *   /           - 返回部署成功信息
 *   /today      - 今日壁纸（302 重定向到图片）
 *   /random     - 随机壁纸（302 重定向到图片）
 *   /all        - 分页查询壁纸 JSON 数据
 *   /total      - 返回数据总数
 *   /favicon.ico - 返回网站图标
 */

// Node.js 内置模块：fs 用于读取本地文件，path 用于路径拼接
const fs = require("fs");
const path = require("path");

// 当前 API 版本号
const VERSION = "4.0.0";
// 必应官方壁纸接口地址
const BINGAPI = "https://bing.com/HPImageArchive.aspx";
// 必应官网根地址，用于拼接图片完整 URL
const BINGURL = "https://bing.com";
// 支持的地区列表（每个地区对应一份独立的 data/<mkt>_all.json 数据文件）
const LOCATIONS = ["de-DE", "en-CA", "en-GB", "en-IN", "en-US", "fr-FR", "it-IT", "ja-JP", "zh-CN"];
// 支持的图片宽度列表（与原版 settings.W 对齐）
const WIDTHS = [1920, 1366, 1280, 1080, 1024, 800, 768, 720, 640, 480, 400, 320, 240];
// 支持的图片高度列表（与原版 settings.H 对齐）
const HEIGHTS = [1920, 1200, 1080, 768, 600, 480, 1280, 800, 240, 320];
// 默认地区
const DEFAULT_MKT = "zh-CN";
// 数据文件中存储的默认分辨率，用于做字符串替换
const DEFAULT_WH = "1920x1080";
// 按年份查询时单页最大返回条数（闰年天数）
const YEAR_LIMIT = 366;
// 普通查询时单页最大返回条数
const LIMIT_DATA = 100;

// JSON 接口统一响应头：声明内容类型、允许跨域、禁止缓存
const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
  "Cache-Control": "no-cache, no-store, must-revalidate",
};

/**
 * 构造成功响应体（与原版 BingResponse.success 对齐）
 * @param {string} msg - 提示信息
 * @param {*} data - 附加数据，可选
 * @returns {{code:number, msg:string, data?:*}}
 */
function success(msg, data) {
  const res = { code: 200, msg: msg };
  if (data !== undefined && data !== null) res.data = data;
  return res;
}

/**
 * 构造分页成功响应体（与原版 BingResponse.table_success 对齐）
 * @param {Array} data - 当前页数据列表
 * @param {number} total - 符合条件的总记录数
 * @returns {{code:number, msg:string, data:Array, total:number}}
 */
function tableSuccess(data, total) {
  const res = { code: 200, msg: "操作成功", data: data, total: total };
  return res;
}

/**
 * 构造错误响应体（与原版 BingResponse.error 对齐）
 * @param {string} msg - 错误信息
 * @returns {{code:number, msg:string}}
 */
function error(msg) {
  return { code: 500, msg: msg };
}

/**
 * 包装为 Netlify Functions 要求的返回对象（JSON 响应）
 * @param {number} statusCode - HTTP 状态码
 * @param {object} body - 响应体对象，会被 JSON 序列化
 * @returns {{statusCode:number, headers:object, body:string}}
 */
function json(statusCode, body) {
  return { statusCode: statusCode, headers: JSON_HEADERS, body: JSON.stringify(body) };
}

/**
 * 构造 302 重定向响应（/today 和 /random 接口使用）
 * @param {string} url - 目标跳转地址
 * @returns {{statusCode:number, headers:object, body:string}}
 */
function redirect(url) {
  return {
    statusCode: 302,
    headers: { Location: url, "Access-Control-Allow-Origin": "*" },
    body: "",
  };
}

/* ---------- 工具函数 ---------- */

/**
 * 在多个候选路径中查找并读取文件（兜底机制，避免 Netlify 部署后工作目录变化导致找不到文件）
 * @param {string} relativePath - 相对路径，如 "data/zh-CN_all.json"
 * @returns {Buffer|null} 文件内容 Buffer，找不到返回 null
 */
function findFile(relativePath) {
  // 候选路径：当前工作目录、函数文件所在目录、项目根目录
  const candidates = [
    path.join(process.cwd(), relativePath),
    path.join(__dirname, relativePath),
    path.join(__dirname, "..", "..", "..", relativePath),
  ];
  for (const p of candidates) {
    try {
      return fs.readFileSync(p);
    } catch (e) {}
  }
  return null;
}

/**
 * 读取指定地区的壁纸 JSON 数据文件
 * @param {string} mkt - 地区码，如 "zh-CN"
 * @returns {object|null} 解析后的 JSON 对象，失败返回 null
 */
function readJson(mkt) {
  const buf = findFile(path.join("data", mkt + "_all.json"));
  if (buf === null) return null;
  try {
    return JSON.parse(buf.toString("utf8"));
  } catch (e) {
    return null;
  }
}

/**
 * 替换壁纸 URL 中的分辨率，实现按需返回不同尺寸的图片
 * @param {string} url - 原始图片 URL（包含 1920x1080）
 * @param {string} wh - 目标分辨率，如 "1366x768" 或 "UHD"
 * @returns {string} 替换后的 URL
 */
function replaceResolution(url, wh) {
  return url.split(DEFAULT_WH).join(wh);
}

/**
 * 归一化请求路径：去除 Netlify 函数路径前缀（/.netlify/functions/api），得到用户原始请求路径
 * @param {object} event - Netlify 事件对象
 * @returns {string} 归一化后的路径，如 "/all"
 */
function normalizePath(event) {
  let p = event.path || "/";
  // 去除 /.netlify/functions/xxx 前缀
  p = p.replace(/^\/\.netlify\/functions\/[^/]+/, "");
  if (p === "" ) p = "/";
  if (!p.startsWith("/")) p = "/" + p;
  return p;
}

/**
 * 校验 /all 接口的查询参数（与原版 util.check_params 对齐）
 * @param {number} page - 页码
 * @param {number} limit - 每页条数
 * @param {string} order - 排序方式 desc/asc
 * @param {number} w - 宽度
 * @param {number} h - 高度
 * @param {boolean} uhd - 是否 4K
 * @param {string} mkt - 地区码
 * @param {number|null} year - 年份过滤
 * @returns {boolean} 参数是否合法
 */
function checkParams(page, limit, order, w, h, uhd, mkt, year) {
  if (!LOCATIONS.includes(mkt)) return false;      // 地区必须在支持列表内
  if (order !== "desc" && order !== "asc") return false; // 排序方式仅支持 desc/asc
  const maxLimit = year ? YEAR_LIMIT : LIMIT_DATA; // 年份查询放宽到 366，否则最大 100
  if (page <= 0 || limit <= 0 || limit > maxLimit) return false;
  if (w === h) return false;                        // 宽高不能相等
  if ((!uhd && !WIDTHS.includes(w)) || !HEIGHTS.includes(h)) return false; // 宽高必须合法
  return true;
}

/**
 * 从查询参数中解析目标分辨率字符串
 * @param {object} q - 查询参数对象
 * @returns {string} 分辨率字符串，如 "1920x1080" 或 "UHD"
 */
function getWh(q) {
  return q.uhd === "true" ? "UHD" : (q.w || "1920") + "x" + (q.h || "1080");
}

/* ---------- Netlify Functions 入口 ---------- */

/**
 * Netlify Functions 的主处理函数
 * @param {object} event - 请求事件对象，包含 path、queryStringParameters 等
 * @returns {Promise<object>} 响应对象（符合 AWS Lambda 响应格式）
 */
exports.handler = async (event) => {
  // 归一化请求路径，并获取查询参数
  const route = normalizePath(event);
  const q = event.queryStringParameters || {};

  try {
    // 路由：/  - 返回部署成功信息与当前版本
    if (route === "/") {
      return json(200, success("BingAPI 部署成功，详情可查看文档：https://api-bimg-cc.apifox.cn", { current_version: VERSION }));
    }

    // 路由：/favicon.ico - 返回网站图标（以 base64 编码二进制）
    if (route === "/favicon.ico") {
      const buf = findFile("favicon.ico");
      if (buf === null) return json(404, error("favicon not found"));
      return {
        statusCode: 200,
        isBase64Encoded: true,
        headers: { "Content-Type": "image/jpeg", "Cache-Control": "no-cache" },
        body: buf.toString("base64"),
      };
    }

    // 路由：/today - 今日壁纸，实时请求必应官方接口并 302 重定向
    if (route === "/today") {
      const mkt = LOCATIONS.includes(q.mkt) ? q.mkt : DEFAULT_MKT; // 地区校验
      const res = await fetch(BINGAPI + "?format=js&n=1&idx=0&mkt=" + mkt);
      const data = await res.json();
      // 拼接完整 URL，并去除必应返回的额外参数，只保留图片地址
      const url = BINGURL + data.images[0].url.replace("&rf=LaDigue_1920x1080.jpg&pid=hp", "");
      return redirect(replaceResolution(url, getWh(q)));
    }

    // 路由：/random - 随机壁纸，从本地 JSON 数据中随机取一条并重定向
    if (route === "/random") {
      const mkt = LOCATIONS.includes(q.mkt) ? q.mkt : DEFAULT_MKT;
      const raw = readJson(mkt);
      if (raw === null || !raw.data || raw.data.length === 0) {
        return json(200, error("暂无数据"));
      }
      // 从数据数组中随机选取一条
      const item = raw.data[Math.floor(Math.random() * raw.data.length)];
      return redirect(replaceResolution(item.url, getWh(q)));
    }

    // 路由：/all - 分页查询壁纸 JSON 数据
    if (route === "/all") {
      // 解析查询参数
      const page = parseInt(q.page || "1", 10);        // 页码，默认 1
      const limit = parseInt(q.limit || "10", 10);     // 每页条数，默认 10
      const order = q.order || "desc";                 // 排序方式，默认降序
      const w = parseInt(q.w || "1920", 10);           // 图片宽度
      const h = parseInt(q.h || "1080", 10);           // 图片高度
      const uhd = q.uhd === "true";                    // 是否 4K
      const mkt = q.mkt || DEFAULT_MKT;                // 地区
      const year = q.year ? parseInt(q.year, 10) : null; // 年份过滤，可选

      // 校验年份参数（>= 2016）
      if (q.year && (isNaN(year) || year < 2016)) {
        return json(200, error("年份参数错误，要求年份>=2016"));
      }
      // 校验全部参数
      if (!checkParams(page, limit, order, w, h, uhd, mkt, year)) {
        return json(200, error("请求参数错误"));
      }

      // 读取对应地区的本地 JSON 数据
      const raw = readJson(mkt);
      if (raw === null) return json(200, error("数据文件不存在"));

      let arr = raw.data || [];
      // 年份过滤：datetime 字段以 "YYYY-" 开头
      if (year !== null) {
        arr = arr.filter((item) => typeof item.datetime === "string" && item.datetime.indexOf(year + "-") === 0);
      }
      // 升序时反转数组（原始数据按时间降序存储）
      if (order === "asc") arr = arr.slice().reverse();

      const total = arr.length;
      const wh = uhd ? "UHD" : w + "x" + h;
      // 分页截取并替换图片分辨率
      const data = arr.slice((page - 1) * limit, page * limit).map((item) => {
        const copy = Object.assign({}, item);
        copy.url = replaceResolution(item.url, wh);
        return copy;
      });
      return json(200, tableSuccess(data, total));
    }

    // 路由：/total - 返回指定地区的数据总条数
    if (route === "/total") {
      const mkt = q.mkt || DEFAULT_MKT;
      if (!LOCATIONS.includes(mkt)) return json(200, error("请求参数错误"));
      const raw = readJson(mkt);
      if (raw === null) return json(200, error("数据文件不存在"));
      return json(200, success("操作成功", raw.data ? raw.data.length : 0));
    }

    // 未匹配到任何路由，返回 404
    return json(404, error("接口不存在: " + route));
  } catch (e) {
    // 全局异常捕获：打印错误日志并返回 500
    console.error(e);
    return json(500, { code: 500, msg: "Function error: " + e.message });
  }
};
