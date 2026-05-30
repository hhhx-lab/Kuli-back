<template>
  <aside
    v-if="visible"
    class="xiaoku"
    :class="[motionState, { open, sleep, reduced, muted }]"
    :style="{ transform: `translate(${offset.x}px, ${offset.y}px)` }"
    @mouseenter="hovering = true"
    @mouseleave="hovering = false"
    @mousemove="wake"
  >
    <button v-if="bubble && !open" class="xiaoku-bubble" type="button" @click="openPanel">
      {{ bubble }}
    </button>

    <button class="xiaoku-face xiaoku-3d" type="button" @click="togglePanel" aria-label="打开小酷">
      <canvas ref="canvasRef" class="xiaoku-canvas" width="180" height="180" aria-hidden="true" />
      <span class="xiaoku-fallback" aria-hidden="true">K</span>
      <span class="xiaoku-status">{{ stateLabel }}</span>
    </button>

    <section v-if="open" class="xiaoku-panel">
      <div class="section-head compact">
        <strong>小酷</strong>
        <div class="xiaoku-controls">
          <button type="button" title="别跟着我" @click="toggleFollow">{{ followMouse ? "定" : "跟" }}</button>
          <button type="button" title="减少动画" @click="toggleReduced">{{ reduced ? "动" : "静" }}</button>
          <button type="button" title="静音" @click="toggleMuted">{{ muted ? "声" : "默" }}</button>
          <button type="button" title="隐藏本页" @click="hideForPage">×</button>
        </div>
      </div>
      <p>{{ answer }}</p>
      <div v-if="draft" class="xiaoku-draft">
        <strong>小纸条草稿</strong>
        <span>{{ draft.summary }}</span>
        <small v-if="draft.missingFields.length">还可以补：{{ draft.missingFields.join("、") }}</small>
      </div>
      <div v-if="citations.length" class="xiaoku-citations" aria-label="小酷引用">
        <span>参考</span>
        <NuxtLink v-for="citation in citations" :key="citation.to" :to="citation.to">{{ citation.title }}</NuxtLink>
      </div>
      <div class="xiaoku-quick-actions">
        <NuxtLink v-for="action in quickActions" :key="action.to + action.label" :to="action.to">{{ action.label }}</NuxtLink>
      </div>
      <div class="chat-row">
        <input v-model="message" placeholder="问问服务、材料或订单状态" @focus="setState('calm')" @keyup.enter="send" />
        <button type="button" @click="send">问</button>
      </div>
      <NuxtLink v-for="action in actions" :key="action.to" :to="action.to">{{ action.label }}</NuxtLink>
    </section>
  </aside>
</template>

<script setup lang="ts">
import type * as Three from "three";

type XiaokuState = "idle" | "curious" | "thinking" | "happy" | "alert" | "sleep" | "hide" | "calm";

const api = useApi();
const auth = useAuthStore();
const route = useRoute();
const open = ref(false);
const sleep = ref(false);
const visible = ref(true);
const reduced = ref(false);
const muted = ref(false);
const followMouse = ref(true);
const hovering = ref(false);
const hasPointer = ref(false);
const message = ref("");
const answer = ref("我在这儿。说不清也没关系，先给我看看。");
const actions = ref<Array<{ label: string; to: string }>>([{ label: "写小纸条", to: "/note" }]);
const citations = ref<Array<{ title: string; to: string; source?: string | null }>>([]);
const draft = ref<{ serviceSlug: string; summary: string; missingFields: string[] } | null>(null);
const sessionId = ref("");
const motionState = ref<XiaokuState>("idle");
const bubble = ref("");
const canvasRef = ref<HTMLCanvasElement | null>(null);
const pointer = reactive({ x: 0, y: 0 });
const offset = reactive({ x: 0, y: 0 });
const quickActions = computed(() => pageContext(route.path).actions);
const stateLabel = computed(() => ({ idle: "online", curious: "scan", thinking: "think", happy: "done", alert: "check", sleep: "sleep", hide: "mini", calm: "calm" })[motionState.value]);

let frame = 0;
let ThreeRuntime: typeof import("three") | null = null;
let renderer: Three.WebGLRenderer | null = null;
let scene: Three.Scene | null = null;
let camera: Three.PerspectiveCamera | null = null;
let cat: Three.Group | null = null;
let tail: Three.Mesh | null = null;
let halo: Three.Group | null = null;
let lastAction = 0;
let sleepTimer = 0;
let hintTimer = 0;

onMounted(async () => {
  await auth.restore();
  const storageKey = `kuli-xiaoku-hidden:${location.pathname}`;
  visible.value = localStorage.getItem(storageKey) !== "true";
  reduced.value = localStorage.getItem("kuli-xiaoku-reduced") === "true";
  muted.value = localStorage.getItem("kuli-xiaoku-muted") === "true";
  followMouse.value = localStorage.getItem("kuli-xiaoku-follow") !== "false";
  let visitorId = localStorage.getItem("kuli-visitor");
  if (!visitorId) {
    visitorId = crypto.randomUUID();
    localStorage.setItem("kuli-visitor", visitorId);
  }
  const session = await api.createAgentSession({ pagePath: location.pathname, visitorId }, auth.token);
  sessionId.value = session.session.id;
  await initThree();
  showPageHint();
  scheduleSleep();
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("scroll", onUserBusy, { passive: true });
  window.addEventListener("focusin", onFocusIn);
  animate();
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("scroll", onUserBusy);
  window.removeEventListener("focusin", onFocusIn);
  window.clearTimeout(sleepTimer);
  window.clearTimeout(hintTimer);
  window.cancelAnimationFrame(frame);
  renderer?.dispose();
});

watch(
  () => route.path,
  () => {
    bubble.value = "";
    offset.x = 0;
    offset.y = 0;
    hasPointer.value = false;
    showPageHint();
  }
);

async function initThree() {
  if (!canvasRef.value) return;
  ThreeRuntime = await import("three");
  const THREE = ThreeRuntime;
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(0, 0.15, 5.2);
  renderer = new THREE.WebGLRenderer({ canvas: canvasRef.value, alpha: true, antialias: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(180, 180, false);
  scene.add(new THREE.AmbientLight(0xffffff, 1.8));
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
  keyLight.position.set(2, 3, 4);
  scene.add(keyLight);
  const purpleLight = new THREE.PointLight(0x9c5cff, 12, 8);
  purpleLight.position.set(-2.4, 1.4, 2);
  scene.add(purpleLight);
  cat = createCat();
  scene.add(cat);
}

function createCat() {
  const THREE = assertThree();
  const group = new THREE.Group();
  const black = new THREE.MeshStandardMaterial({ color: 0x111117, roughness: 0.58, metalness: 0.22 });
  const white = new THREE.MeshStandardMaterial({ color: 0xf4f0ea, roughness: 0.48 });
  const purple = new THREE.MeshStandardMaterial({ color: 0x8f4bff, emissive: 0x5f22c8, emissiveIntensity: 0.4, roughness: 0.35, metalness: 0.35 });
  const eye = new THREE.MeshStandardMaterial({ color: 0xb077ff, emissive: 0x8f4bff, emissiveIntensity: 0.8 });

  const body = new THREE.Mesh(new THREE.SphereGeometry(0.72, 32, 20), black);
  body.scale.set(0.78, 1.08, 0.58);
  body.position.y = -0.35;
  group.add(body);

  const chest = new THREE.Mesh(new THREE.SphereGeometry(0.32, 24, 16), white);
  chest.scale.set(0.72, 1.1, 0.32);
  chest.position.set(0, -0.25, 0.47);
  group.add(chest);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.6, 32, 20), black);
  head.position.set(0, 0.62, 0.02);
  group.add(head);

  for (const side of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.52, 4), black);
    ear.position.set(side * 0.37, 1.08, -0.02);
    ear.rotation.set(0.12, 0, side * 0.46);
    group.add(ear);
    const inner = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.32, 4), purple);
    inner.position.set(side * 0.36, 1.06, 0.04);
    inner.rotation.copy(ear.rotation);
    group.add(inner);
  }

  const muzzle = new THREE.Mesh(new THREE.SphereGeometry(0.26, 24, 16), white);
  muzzle.scale.set(1.25, 0.72, 0.45);
  muzzle.position.set(0, 0.48, 0.5);
  group.add(muzzle);

  for (const side of [-1, 1]) {
    const eyeMesh = new THREE.Mesh(new THREE.SphereGeometry(0.055, 16, 12), eye);
    eyeMesh.scale.set(1.4, 0.72, 0.6);
    eyeMesh.position.set(side * 0.2, 0.68, 0.53);
    group.add(eyeMesh);
    const paw = new THREE.Mesh(new THREE.SphereGeometry(0.15, 20, 12), white);
    paw.scale.set(1.18, 0.58, 0.88);
    paw.position.set(side * 0.28, -1.06, 0.33);
    group.add(paw);
  }

  const collar = new THREE.Mesh(new THREE.TorusGeometry(0.43, 0.026, 8, 48), purple);
  collar.position.set(0, 0.2, 0.05);
  collar.rotation.x = Math.PI / 2;
  group.add(collar);

  const badge = makeBadge();
  badge.position.set(0, 0.03, 0.55);
  group.add(badge);

  tail = new THREE.Mesh(
    new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new THREE.Vector3(0.42, -0.72, -0.12), new THREE.Vector3(0.9, -0.22, -0.1), new THREE.Vector3(0.72, 0.38, 0.06)]), 32, 0.055, 10),
    black
  );
  group.add(tail);

  halo = new THREE.Group();
  for (let i = 0; i < 2; i += 1) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.92 + i * 0.16, 0.008, 8, 90), purple);
    ring.rotation.set(Math.PI / 2.45, 0.2 + i * 0.18, 0);
    halo.add(ring);
  }
  halo.position.y = 0.04;
  group.add(halo);

  group.scale.setScalar(1.05);
  return group;
}

function makeBadge() {
  const THREE = assertThree();
  const badgeCanvas = document.createElement("canvas");
  badgeCanvas.width = 128;
  badgeCanvas.height = 128;
  const ctx = badgeCanvas.getContext("2d");
  if (ctx) {
    ctx.fillStyle = "#0d0d12";
    ctx.fillRect(0, 0, 128, 128);
    ctx.strokeStyle = "#8f4bff";
    ctx.lineWidth = 8;
    ctx.strokeRect(12, 12, 104, 104);
    ctx.fillStyle = "#f4f0ea";
    ctx.font = "bold 74px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("K", 64, 68);
  }
  const texture = new THREE.CanvasTexture(badgeCanvas);
  const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true });
  const badge = new THREE.Mesh(new THREE.PlaneGeometry(0.28, 0.28), material);
  return badge;
}

function assertThree() {
  if (!ThreeRuntime) throw new Error("Three.js has not loaded yet");
  return ThreeRuntime;
}

function animate(time = 0) {
  const state = reduced.value ? "calm" : motionState.value;
  if (hasPointer.value && followMouse.value && !reduced.value && !open.value && !hovering.value && !isDenseRoute(route.path)) {
    const targetX = Math.max(-72, Math.min(10, pointer.x - window.innerWidth + 132));
    const targetY = Math.max(-92, Math.min(10, pointer.y - window.innerHeight + 132));
    offset.x += (targetX - offset.x) * 0.035;
    offset.y += (targetY - offset.y) * 0.035;
  }
  if (cat && renderer && scene && camera) {
    const t = time / 1000;
    const bob = state === "sleep" || state === "hide" ? -0.04 : Math.sin(t * 2.4) * 0.035;
    const happyJump = state === "happy" ? Math.abs(Math.sin(t * 8)) * 0.18 : 0;
    const alertShake = state === "alert" ? Math.sin(t * 18) * 0.07 : 0;
    cat.position.y = bob + happyJump;
    cat.rotation.y += (((pointer.x / Math.max(window.innerWidth, 1)) - 0.5) * 0.38 + alertShake - cat.rotation.y) * 0.05;
    cat.rotation.x += ((state === "sleep" ? -0.12 : 0.02) - cat.rotation.x) * 0.04;
    if (tail) tail.rotation.z = Math.sin(t * (state === "happy" ? 8 : 2.4)) * 0.18;
    if (halo) halo.rotation.z += state === "thinking" ? 0.045 : 0.01;
    renderer.render(scene, camera);
  }
  maybeFreeMotion();
  frame = window.requestAnimationFrame(animate);
}

function maybeFreeMotion() {
  if (reduced.value || open.value || motionState.value === "sleep" || motionState.value === "hide") return;
  const now = Date.now();
  if (now - lastAction < 14000) return;
  lastAction = now;
  setState(Math.random() > 0.5 ? "curious" : "happy", 3600);
}

function pageContext(path: string) {
  if (path.startsWith("/services/")) {
    return { state: "curious" as XiaokuState, text: "你可以先发一个大概需求，我帮你判断材料够不够。", actions: [{ label: "写小纸条", to: `/note?service=${path.split("/").pop()}` }] };
  }
  if (path === "/services") {
    return { state: "hide" as XiaokuState, text: "不知道选哪类服务的话，可以先问我。", actions: [{ label: "帮我写小纸条", to: "/note" }, { label: "看知识库", to: "/help" }] };
  }
  if (path.startsWith("/note")) {
    return { state: "hide" as XiaokuState, text: "写不完整也没关系，我可以帮你整理。", actions: [{ label: "查看服务", to: "/services" }] };
  }
  if (path.startsWith("/orders")) {
    return { state: "hide" as XiaokuState, text: "我可以解释订单状态和下一步。", actions: [{ label: "我的订单", to: "/orders" }] };
  }
  if (path.startsWith("/notifications")) {
    return { state: "hide" as XiaokuState, text: "我可以帮你解释通知和订单下一步。", actions: [{ label: "我的订单", to: "/orders" }] };
  }
  if (path.startsWith("/legal")) {
    return { state: "hide" as XiaokuState, text: "这里主要是规则说明，我会安静一点。", actions: [{ label: "上传说明", to: "/legal/upload-policy" }] };
  }
  if (path.startsWith("/admin")) {
    return { state: "hide" as XiaokuState, text: "后台信息密集，我先缩在角落。", actions: [{ label: "订单管理", to: "/admin" }] };
  }
  return { state: "curious" as XiaokuState, text: "不知道选哪类服务的话，可以先问我。", actions: [{ label: "帮我写小纸条", to: "/note" }, { label: "查看服务", to: "/services" }] };
}

function showPageHint() {
  const context = pageContext(route.path);
  setState(context.state, context.state === "hide" ? 0 : 5200);
  window.clearTimeout(hintTimer);
  hintTimer = window.setTimeout(() => {
    if (!open.value && !reduced.value && context.state !== "hide" && window.innerWidth > 760) bubble.value = context.text;
  }, 900);
}

function isDenseRoute(path: string) {
  return path === "/services" || path.startsWith("/note") || path.startsWith("/orders") || path.startsWith("/notifications") || path.startsWith("/legal") || path.startsWith("/admin");
}

function setState(state: XiaokuState, resetAfter = 0) {
  motionState.value = state;
  sleep.value = state === "sleep";
  if (resetAfter) {
    window.setTimeout(() => {
      if (!open.value && motionState.value === state) motionState.value = "idle";
    }, resetAfter);
  }
}

function wake() {
  sleep.value = false;
  if (motionState.value === "sleep") motionState.value = "idle";
  scheduleSleep();
}

function scheduleSleep() {
  window.clearTimeout(sleepTimer);
  sleepTimer = window.setTimeout(() => setState("sleep"), 60000);
}

function onPointerMove(event: PointerEvent) {
  wake();
  hasPointer.value = true;
  pointer.x = event.clientX;
  pointer.y = event.clientY;
}

function onUserBusy() {
  bubble.value = "";
  if (!open.value) setState(isDenseRoute(route.path) ? "hide" : "calm", isDenseRoute(route.path) ? 0 : 2600);
}

function onFocusIn(event: FocusEvent) {
  const target = event.target as HTMLElement | null;
  if (target?.matches("input, textarea, select")) setState("calm", 3200);
}

function togglePanel() {
  open.value = !open.value;
  bubble.value = "";
  setState(open.value ? "curious" : "idle", 2400);
}

function openPanel() {
  open.value = true;
  bubble.value = "";
  setState("curious", 2400);
}

function toggleFollow() {
  followMouse.value = !followMouse.value;
  localStorage.setItem("kuli-xiaoku-follow", String(followMouse.value));
}

function toggleReduced() {
  reduced.value = !reduced.value;
  localStorage.setItem("kuli-xiaoku-reduced", String(reduced.value));
}

function toggleMuted() {
  muted.value = !muted.value;
  localStorage.setItem("kuli-xiaoku-muted", String(muted.value));
}

function hideForPage() {
  localStorage.setItem(`kuli-xiaoku-hidden:${location.pathname}`, "true");
  visible.value = false;
}

async function send() {
  if (!message.value.trim() || !sessionId.value) return;
  setState("thinking");
  const response = await api.chat({ sessionId: sessionId.value, message: message.value }, auth.token);
  answer.value = response.answer;
  actions.value = response.actions;
  citations.value = response.citations ?? [];
  draft.value = response.draft ?? null;
  message.value = "";
  setState("happy", 2600);
}
</script>
