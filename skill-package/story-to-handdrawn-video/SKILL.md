---
name: story-to-handdrawn-video
description: Convert Chinese story copy, article-derived drafts, ordered local images, or user-uploaded character IP references into a silent hand-drawn Remotion story video. Supports a locked user-approved colored-pencil diary default, a built-in 20-style library, custom character-reference images, the 海洋哥 IP profile, and a required source-to-draft review gate for article content. Use when the user asks to extract an article into video copy, review or diff that copy, use an uploaded character prototype, use the 海洋哥 IP, generate, import, restyle, preview, or render a hand-drawn story video.
---

# Story to Hand-drawn Video

Use the project renderer through this Skill's `scripts/run_story_video.py`. Set `STORY_VIDEO_PROJECT` when the project is not the current working directory. The wrapper must not rely on an author-specific absolute path.

## Workflow

1. Accept inline Chinese story text, a UTF-8 text file, or ordered local images.
2. Preserve the user's wording. For text input, keep one complete sentence as one beat by default and split only long compound sentences at natural narrative turns.
3. For uploaded composite pages, automatically crop the handwritten caption and illustration, then derive an aligned black-and-white plate locally.
4. In direct-cut mode, keep the order `text → bw_full → color`; reveal every stage from left to right.
5. In page-flip mode, preserve the untouched uploaded master and show it statically before curling the page from the bottom-right corner. Do not add caption, black-and-white, or recoloring stages. Retain a faded version of the source page on the paper underside.
6. Keep all illustration marks inside the white safe border. Use contained framing and never `cover` cropping.
7. Produce a silent MP4. Voiceover and optional BGM are post-production tasks.
8. Report the scene count, duration, output path, and whether the result is plan-only, preview, or final.

## Custom character IP references

When the user uploads a character prototype and says to use it as the IP, pass that image through `--character-reference`. The image is an identity reference, not a scene background: preserve the user-designated person's face, hair, age, body proportions, wardrobe, and any explicitly requested companion character; ignore unrelated background, temporary pose, interface text, and incidental props. If the user supplies a written lock that conflicts with visible prototype details, the uploaded prototype wins unless the user explicitly asks for the change.

For the user's named IP, “海洋哥” or “海洋叔叔”, use the registered profile and the uploaded prototype image together:

```bash
python3 scripts/run_story_video.py \
  --input /absolute/story.txt \
  --character-profile haiyangge \
  --character-reference /absolute/uploaded-character-prototype.png \
  --mode generate
```

The `haiyangge` profile applies this lock: `固定IP：海洋叔叔，圆脸、短黑发、蓝色工装、棕色皮鞋；所有场景保持脸型、发型、服装和身体比例一致。` The uploaded prototype remains the primary visual source and is required; do not synthesize the named IP from text alone when no prototype image is available.

For any other custom IP, use `--character-reference` with an optional `--character-lock`:

```bash
python3 scripts/run_story_video.py \
  --input /absolute/story.txt \
  --character-reference /absolute/custom-character.png \
  --character-lock "固定IP：保留上传原型中的脸型、发型、服装和体态；所有场景保持一致。" \
  --mode generate
```

The reference is included in every Codex Image2 scene job and in the API fallback's image references. Changing the reference image changes the generated asset fingerprint, so stale images are not silently reused. The uploaded image is read from the user's local path and is not copied into the public repository.

Typical user requests that should trigger this path:

- “以我上传的这张人物图为指定 IP，把这篇政策文章做成手绘解读视频。”
- “以海洋哥 IP 形象制作这期设备管理培训短片，原型图以我上传的图片为准。”
- “用我上传的工程师角色原型，把这套生产线安全操作流程做成连续手绘动画。”
- “用我上传的品牌吉祥物和主人物形象，把产品故事做成可后期配音的手绘视频。”

## Article-content review gate

When the input comes from an article URL or other source material, stop after content extraction and obtain explicit user approval before generating images, narration, or a final video.

1. Save a UTF-8 source snapshot and the proposed video copy as separate text files. Preserve names, dates, figures, quotations, policy terms, and logical relationships; mark any inference.
2. Run the deterministic review command:

   ```bash
   python3 scripts/run_story_video.py \
     --mode review \
     --source /absolute/article-source.txt \
     --input /absolute/story-draft.txt \
     --review-dir /absolute/story-review
   ```

   This writes `story-review.md`, `story-review.diff`, and `story-review.json`. The diff compares source units with proposed video beats and is a review aid, not a substitute for factual checking.
3. Show the report and diff to the user, then pause. Accept edits to `story-draft.txt`; rerun review whenever the draft changes.
4. After the user explicitly confirms the current wording, create the approval record:

   ```bash
   python3 scripts/run_story_video.py \
     --mode approve \
     --input /absolute/story-draft.txt \
     --review-manifest /absolute/story-review/story-review.json
   ```

5. Pass the resulting `story-review.approval.json` to `--approved-review` for `generate` or `full`. The hash check must pass before generation. Never reuse an approval record after editing the draft.

For direct user-supplied story text that is not derived from an article, `--mode plan` remains available; still pause for approval whenever the user asks to review the copy first.

## Default visual lock

The immutable default style id is `colored-pencil-diary`. When the user does not request another style, preserve these fixed project resources:

- `references/target-diary-style.txt`: prompt-ready visual grammar.
- `references/style-bw.png`: black-and-white mark-making board.
- `references/style-color.png`: colored-pencil technique and palette board.
- `references/style-layout.png`: full-page caption and composition board.
- `references/style-approved.png`: user-approved final-output anchor and default quality bar.

Treat the boards as style evidence only. Ignore their depicted people, actions, props, dates, and Chinese wording. Let the character sheet control identity and continuity. When visual instructions conflict or remain ambiguous, follow `style-approved.png` for line weight, pencil density, figure scale, facial simplicity, negative space, and final finish.

Match these non-negotiable traits: pure white digital page; blunt wobbly black felt-tip contours; oversized rounded heads and short compact bodies; simple expressive faces; visible short colored-pencil strokes with white gaps; a small dusty-blue, brick-red, charcoal, beige, tan, muted-yellow, and light-gray palette; sparse contextual props and abundant unfilled white space. Avoid anime, vector polish, smooth fills, watercolor, gradients, realistic lighting, paper grain, and dense scenery.

Do not replace or bypass the fixed default resources unless the user explicitly requests a different visual family. The renderer fingerprints the selected recipe and its reference images, so switching styles automatically creates a new generated-asset batch instead of reusing stale images.

## Built-in style library

The machine-readable source of truth is `<project>/references/handdrawn-style-library.json`. Use `python3 scripts/run_story_video.py --list-styles` to show the current menu. `--style` accepts the order number, id, Chinese name, English name, or any registered alias. Use the catalog-level `contact_sheet` and each style's `example_image` to compare visual families before selection; treat those images as style evidence, not scene or character references.

| # | Style id | 中文名 | Best fit |
|---:|---|---|---|
| 1 | `colored-pencil-diary` | 彩铅日记漫画（默认） | 家庭、生活、纪实情感 |
| 2 | `minimal-line-explainer` | 极简黑白线条讲解 | 科普、流程、观点 |
| 3 | `kid-crayon` | 五岁儿童蜡笔坏画 | 童年、亲子、轻喜剧 |
| 4 | `rawkid-crayon` | 潦草家庭投稿蜡笔 | 家庭连载、温暖日常 |
| 5 | `bean-doodle-infographic` | 小豆人涂鸦信息图 | 步骤、清单、知识卡 |
| 6 | `ms-paint-bad-doodle` | 鼠标烂涂鸦 | 吐槽、反转、荒诞 |
| 7 | `ballpoint-scribble` | 圆珠笔缠绕线速写 | 肖像、动物、独白 |
| 8 | `real-crayon-paper` | 真实蜡笔纸实拍 | 儿童视角、成长记录 |
| 9 | `ink-wash` | 水墨写意 | 文化、寓言、感悟 |
| 10 | `emotional-watercolor-sketch` | 情绪叙事淡彩速写 | 回忆、关系、克制纪实 |
| 11 | `retro-gouache-concept` | 中古动画水粉概念稿 | 怀旧、城市、温暖剧情 |
| 12 | `sunlit-storybook` | 暖光童画绘本 | 治愈、童话、亲情 |
| 13 | `nordic-gouache-storybook` | 北欧低饱和水粉绘本 | 安静日常、自然、睡前故事 |
| 14 | `inked-storybook` | 墨线淡彩绘本 | 角色、青春、对白 |
| 15 | `warm-flat-storybook` | 暖色几何扁平绘本 | 关系、品牌、轻科普 |
| 16 | `naive-marker-notes` | 稚拙马克笔笔记 | 社媒、观点、年轻化内容 |
| 17 | `zine-riso-collage` | Zine 孔版拼贴 | 成长、旅行、音乐文化 |
| 18 | `organic-contour-doodle` | 有机轮廓品牌涂鸦 | 生活方式、餐饮、品牌故事 |
| 19 | `whiteboard-explainer` | 白板讲解动画 | 教程、商业解释、时间线 |
| 20 | `linocut-editorial` | 粗粝木刻社论插画 | 社会议题、历史、寓言 |

When the user names a style, use it directly. When the user asks for options without naming one, recommend 3–5 styles based on story content instead of forcing a 20-item clarification. Never blend two recipes unless the user explicitly requests a hybrid. Keep character identity, safe framing, narrative isolation, and text accuracy independent of style.

Only the default style currently has fixed visual reference boards. Other styles are prompt-locked and must not inherit the default colored-pencil boards. Their recipe, caption handwriting, palette, negative constraints, source provenance, and aliases are all stored in the library. Repo-derived recipes retain MIT attribution in `<project>/references/handdrawn-styles-LICENSE.txt`.

## Uploaded images

Preview:

```bash
python3 scripts/run_story_video.py \
  --images /absolute/01.jpg /absolute/02.jpg \
  --title "故事标题" \
  --mode preview \
  --transition cut
```

Final direct-cut render:

```bash
python3 scripts/run_story_video.py \
  --images /absolute/01.jpg /absolute/02.jpg \
  --title "故事标题" \
  --mode full \
  --transition cut \
  --page-duration 4.4
```

Final page-flip render:

```bash
python3 scripts/run_story_video.py \
  --images /absolute/01.jpg /absolute/02.jpg \
  --title "故事标题" \
  --mode full \
  --transition page-flip \
  --transition-sec 0.7
```

Use `--layout auto|composite|full` to control how uploaded pages are interpreted.

## Story text

Plan without generating images:

```bash
python3 scripts/run_story_video.py \
  --input /absolute/story.txt \
  --title "故事标题" \
  --style colored-pencil-diary \
  --mode plan
```

Use a different built-in style:

```bash
python3 scripts/run_story_video.py \
  --input /absolute/story.txt \
  --title "故事标题" \
  --style ink-wash \
  --mode generate
```

Prepare Codex Image2 jobs, then import and render:

```bash
python3 scripts/run_story_video.py --input /absolute/story.txt --title "故事标题" --mode generate
python3 scripts/run_story_video.py --mode import
python3 scripts/run_story_video.py --mode render
```

Use `--generator codex` by default. Use `--generator api` only when the user explicitly selects the API fallback and `OPENAI_API_KEY` is available. Use `--force` only when the user explicitly wants an existing generated batch replaced.

Default to `--text-mode font` so the user's Chinese wording remains exact. Use `--text-mode image2` only when the user explicitly prioritizes source-like handwritten captions and accepts that generated Chinese glyphs may need correction.

For time jumps, ambiguous pronouns, medical scenes, or age-sensitive characters, provide a JSON visual plan keyed by two-digit scene id through `--visual-plan`.

## Output contract

- Text-story final: `<project>/out/picture_silent.mp4`
- Text-story preview: `<project>/out/picture_silent-preview.mp4`
- Uploaded-image final: `<project>/out/uploaded_picture_silent.mp4`
- Uploaded-image preview: `<project>/out/uploaded_picture_silent-preview.mp4`
- Resolution: final 1080×1440; preview 720×960
- Codec/audio: H.264, silent

After changing the renderer or style library, run the deterministic style-list command and one plan-only smoke test. Do not spend image-generation credits solely for validation unless the user requests visual samples.
