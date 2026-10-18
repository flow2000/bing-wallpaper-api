/*
 * Bing Wallpaper API - Cloudflare Workers 入口
 *
 * 功能说明：
 * 本文件是部署在 Cloudflare Workers 上的边缘函数，提供必应壁纸的查询接口。
 * Workers 仅支持 JS/TS 运行时，因此与 Netlify 版本（netlify/functions/api.js）一样使用 JavaScript 实现。
 *
 * 数据来源：
 * - /today 接口：实时请求必应官方接口，返回最新壁纸
 * - /random、/all、/total 接口：运行时从 GitHub raw 拉取 data/<mkt>_all.json
 *   （data 目录总计约 8MB，超出 Workers 免费套餐 1MiB 打包限制，故不随 Worker 打包；
 *     拉取结果在 Cloudflare 边缘缓存 1 小时，每日数据更新无需重新部署）
 *
 * 路由列表：
 *   /           - 返回部署成功信息（支持 HEAD 探活）
 *   /today      - 今日壁纸（302 重定向到图片）
 *   /random     - 随机壁纸（302 重定向到图片）
 *   /all        - 分页查询壁纸 JSON 数据
 *   /total      - 返回数据总数
 *   /favicon.ico - 返回网站图标
 */

// favicon.ico 以 Data 模块形式打包（见 wrangler.toml 的 rules 配置），内容为 ArrayBuffer
import faviconIco from "../favicon.ico";

// 当前 API 版本号（与 settings.VERSION、start.sh、netlify/functions/api.js 保持一致）
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

// 数据文件默认基准地址（上游仓库 master 分支 data 目录），可通过环境变量 DATA_BASE 覆盖（Fork 部署时修改）
const DEFAULT_DATA_BASE = "https://raw.githubusercontent.com/flow2000/bing-wallpaper-api/master/data";
// 数据 JSON 在 Cloudflare 边缘的缓存时间（秒），与接口缓存策略一致：1 小时
const DATA_CACHE_TTL = 3600;

// ---------- CDN 缓存策略 ----------
// 每日更新的数据（/today、/all、/total、/）：缓存 1 小时
const CACHE_DAILY = "public, max-age=3600, s-maxage=3600";
// 静态资源（/favicon.ico）：缓存 1 年且不可变
const CACHE_STATIC = "public, max-age=31536000, immutable";
// 随机接口（/random）及错误响应：禁止缓存
const CACHE_NONE = "no-store, no-cache, must-revalidate";

// JSON 接口基础响应头：声明内容类型、允许跨域（缓存头按路由动态追加）
const BASE_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Access-Control-Allow-Origin": "*",
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
  return { code: 200, msg: "操作成功", data: data, total: total };
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
 * 构造 JSON 响应
 * @param {object} body - 响应体对象，会被 JSON 序列化
 * @param {string} [cacheControl=CACHE_NONE] - Cache-Control 头值，默认禁止缓存
 * @param {number} [status=200] - HTTP 状态码
 * @returns {Response}
 */
function json(body, cacheControl, status) {
  const headers = new Headers(BASE_HEADERS);
  headers.set("Cache-Control", cacheControl || CACHE_NONE);
  return new Response(JSON.stringify(body), { status: status || 200, headers: headers });
}

/**
 * 构造 302 重定向响应（/today 和 /random 接口使用）
 * @param {string} url - 目标跳转地址
 * @param {string} [cacheControl=CACHE_NONE] - Cache-Control 头值，默认禁止缓存
 * @returns {Response}
 */
function redirect(url, cacheControl) {
  return new Response(null, {
    status: 302,
    headers: {
      Location: url,
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": cacheControl || CACHE_NONE,
    },
  });
}

/* ---------- 工具函数 ---------- */

/**
 * 读取指定地区的壁纸 JSON 数据（从 GitHub raw 拉取，结果在边缘缓存 DATA_CACHE_TTL 秒）
 * @param {object} env - Worker 环境变量
 * @param {string} mkt - 地区码，如 "zh-CN"
 * @returns {Promise<object|null>} 解析后的 JSON 对象，失败返回 null
 */
async function readJson(env, mkt) {
  const base = (env && env.DATA_BASE) || DEFAULT_DATA_BASE;
  try {
    const res = await fetch(base + "/" + mkt + "_all.json", {
      // 强制边缘缓存 1 小时：GitHub raw 默认仅缓存 5 分钟
      cf: { cacheTtl: DATA_CACHE_TTL, cacheEverything: true },
    });
    if (!res.ok) return null;
    return await res.json();
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
 * 校验 /all 接口的查询参数（与原版 util.check_params 对齐）
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

/* ---------- Cloudflare Workers 入口 ---------- */

export default {
  /**
   * Workers 主处理函数
   * @param {Request} request - 请求对象
   * @param {object} env - 环境变量（wrangler.toml 的 [vars] 及 Secrets）
   * @returns {Promise<Response>}
   */
  async fetch(request, env) {
    const url = new URL(request.url);
    const route = url.pathname;
    const q = Object.fromEntries(url.searchParams);

    try {
      // 路由：/  - 返回部署成功信息与当前版本
      if (route === "/") {
        // HEAD 请求：只返回响应头，不返回 body（供部署探活使用）
        if (request.method === "HEAD") {
          const headers = new Headers(BASE_HEADERS);
          headers.set("Cache-Control", CACHE_DAILY);
          return new Response(null, { status: 200, headers: headers });
        }
        return json(success("BingAPI 部署成功，详情可查看文档：https://api-bimg-cc.apifox.cn", { current_version: VERSION }), CACHE_DAILY);
      }

      // 路由：/favicon.ico - 返回网站图标（打包为 Data 模块，直接返回二进制）
      if (route === "/favicon.ico") {
        return new Response(faviconIco, {
          status: 200,
          headers: { "Content-Type": "image/x-icon", "Cache-Control": CACHE_STATIC },
        });
      }

      // 路由：/today - 今日壁纸，实时请求必应官方接口并 302 重定向
      if (route === "/today") {
        const mkt = LOCATIONS.includes(q.mkt) ? q.mkt : DEFAULT_MKT; // 地区校验
        const res = await fetch(BINGAPI + "?format=js&n=1&idx=0&mkt=" + mkt);
        const data = await res.json();
        // 拼接完整 URL，并去除必应返回的额外参数，只保留图片地址
        const imgUrl = BINGURL + data.images[0].url.replace("&rf=LaDigue_1920x1080.jpg&pid=hp", "");
        return redirect(replaceResolution(imgUrl, getWh(q)), CACHE_DAILY);
      }

      // 路由：/random - 随机壁纸，从 JSON 数据中随机取一条并重定向
      if (route === "/random") {
        const mkt = LOCATIONS.includes(q.mkt) ? q.mkt : DEFAULT_MKT;
        const raw = await readJson(env, mkt);
        if (raw === null || !raw.data || raw.data.length === 0) {
          return json(error("暂无数据"), CACHE_NONE, 200);
        }
        // 从数据数组中随机选取一条（必须禁止缓存，保证每次请求结果不同）
        const item = raw.data[Math.floor(Math.random() * raw.data.length)];
        return redirect(replaceResolution(item.url, getWh(q)), CACHE_NONE);
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
          return json(error("年份参数错误，要求年份>=2016"), CACHE_NONE, 200);
        }
        // 校验全部参数
        if (!checkParams(page, limit, order, w, h, uhd, mkt, year)) {
          return json(error("请求参数错误"), CACHE_NONE, 200);
        }

        // 读取对应地区的 JSON 数据
        const raw = await readJson(env, mkt);
        if (raw === null) return json(error("数据文件不存在"), CACHE_NONE, 200);

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
        return json(tableSuccess(data, total), CACHE_DAILY);
      }

      // 路由：/total - 返回指定地区的数据总条数
      if (route === "/total") {
        const mkt = q.mkt || DEFAULT_MKT;
        if (!LOCATIONS.includes(mkt)) return json(error("请求参数错误"), CACHE_NONE, 200);
        const raw = await readJson(env, mkt);
        if (raw === null) return json(error("数据文件不存在"), CACHE_NONE, 200);
        return json(success("操作成功", raw.data ? raw.data.length : 0), CACHE_DAILY);
      }

      // 未匹配到任何路由，返回 404
      return json(error("接口不存在: " + route), CACHE_NONE, 404);
    } catch (e) {
      // 全局异常捕获：返回 500
      return json({ code: 500, msg: "Worker error: " + e.message }, CACHE_NONE, 500);
    }
  },
};
