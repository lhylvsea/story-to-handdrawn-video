# Prior-art research

研究日期：2026-08-09（Asia/Shanghai）

## 检索与证据边界

本次按 `qiaomu-meta-skill` 运行了 3 组 SkillsMP 查询：`hand-drawn video voiceover`、`Remotion audio video`、`subtitle voiceover video`。SkillsMP 返回的是目录元数据；其中 `repo_stars` 表示 GitHub 仓库 star，不是 Skill 安装量、评分或质量结论。`skills.sh` 统一检索器在 Windows 子进程中因本机只有 `npx.cmd`、没有可直接解析的 `npx` 可执行名而失败，记为 `missing evidence`，没有把该目录当作已检索成功。

未执行候选 Skill 的代码。对入选候选只读取了公开的 `SKILL.md` 和目录元数据，未把候选脚本复制进本仓库。

## 候选与具体学习点

### 1. HyperFrames

- 源码：[nexu-io/open-design/design-templates/hyperframes/SKILL.md](https://github.com/nexu-io/open-design/blob/main/design-templates/hyperframes/SKILL.md)
- 目录信号：SkillsMP 在 2026-07-27 的索引中记录其所属仓库约 84,364 GitHub stars；该数字不是 Skill 质量或安装量。
- 具体机制：把视频时间轴、媒体轨道、字幕和 TTS 当作独立可验证的媒体层；要求显式的 `data-start`/`data-duration`，并将音频作为独立 `<audio>` 轨道。
- 本包取舍：保留“音画共用一个明确时间基准”和“字幕不默认混入媒体”的原则；不采用 HTML/GSAP 作为本项目的渲染替代，因为本仓库已有 Remotion 资产流水线。

### 2. video-use

- 源码：[browser-use/video-use/SKILL.md](https://github.com/browser-use/video-use/blob/main/SKILL.md)
- 目录信号：SkillsMP 在 2026-07-01 的索引中记录该仓库约 19,954 GitHub stars；该数字不是 Skill 质量或安装量。
- 具体机制：强调 audio-first、在输出时间轴上处理字幕、用 FFprobe 验证最终时长，并在最终输出上做边界与音频检查。
- 本包取舍：保留 FFprobe 终审、明确的输出轨道映射和无黑帧/音频存在性验证；不采用其多素材剪辑、转录和远程凭据工作流，因为本次变更只针对故事手绘渲染后的配音后期。

### 3. 上游 story-to-handdrawn-video

- 源码：[gnipbao/story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video)
- 具体机制：静音 H.264 画面轨作为核心渲染产物，图片生成、导入、Remotion 渲染和文章审阅分层。
- 本包取舍：保留静音基础轨的兼容性；新增独立后期脚本，不把 TTS 或字幕依赖强行塞进基础 Remotion 合成。

## keep / adapt / reject / invent

- **keep**：独立音频轨、场景时间基准、显式媒体映射、FFprobe 终审、字幕按需生成。
- **adapt**：将最终播放速度固定为可配置参数且默认 `1.2`；使用 FFmpeg `setpts` 与 `atempo` 同步加速画面和旁白，而不是只改变其中一条轨道。
- **reject**：默认烧录字幕、默认生成 SRT/VTT、未审查的远程脚本、与本仓库无关的 HTML 视频引擎迁移。
- **invent**：`postprocess_voiceover.py` 将“逐镜头 TTS → 原时间轴填充 → 1.2 倍同步变速 → 显式视频/音频映射”收束成一个可复用 CLI；字幕模式为 `none|srt`，SRT 即使启用也只作为外挂文件，不进入 MP4。

## 缺失证据

- `skills.sh` 目录检索因 Windows `npx` 可执行名解析失败，未获得该目录的安装信号。
- 没有第三方人工盲评、用户满意度、跨平台真实安装和云端 TTS 对比证据；这些不能由本地单元测试替代。
