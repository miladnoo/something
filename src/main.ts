import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const container = document.getElementById("app") as HTMLDivElement;
const statusEl = document.getElementById("status") as HTMLDivElement;

function setStatus(text: string, isError = false) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", isError);
  statusEl.classList.remove("hidden");
}

function hideStatus() {
  statusEl.classList.add("hidden");
}

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e1a);
scene.fog = new THREE.Fog(0x0a0e1a, 14, 34);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(4.2, 3.2, 6.4);

// ---------------------------------------------------------------- controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1.5, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 3;
controls.maxDistance = 18;
controls.maxPolarAngle = Math.PI * 0.52; // don't go under the floor
controls.autoRotate = true;
controls.autoRotateSpeed = 1.2;
controls.update();

// ---------------------------------------------------------------- lights
const hemi = new THREE.HemisphereLight(0x9fd4ff, 0x1a2035, 0.9);
scene.add(hemi);

const key = new THREE.DirectionalLight(0xffffff, 2.2);
key.position.set(5, 8, 4);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.left = -6;
key.shadow.camera.right = 6;
key.shadow.camera.top = 6;
key.shadow.camera.bottom = -6;
scene.add(key);

const rim = new THREE.DirectionalLight(0x6ea8ff, 0.8);
rim.position.set(-6, 4, -5);
scene.add(rim);

// ---------------------------------------------------------------- floor
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(9, 64),
  new THREE.MeshStandardMaterial({ color: 0x141b2d, roughness: 0.95 })
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

const grid = new THREE.GridHelper(18, 36, 0x2a3550, 0x1c2438);
grid.position.y = 0.001;
scene.add(grid);

// ---------------------------------------------------------------- model
const loader = new GLTFLoader();
loader.load(
  "/models/snowman.glb",
  (gltf) => {
    const model = gltf.scene;

    // Center horizontally, sit on floor
    const bbox = new THREE.Box3().setFromObject(model);
    const center = bbox.getCenter(new THREE.Vector3());
    model.position.x -= center.x;
    model.position.z -= center.z;
    model.position.y -= bbox.min.y;

    model.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        obj.castShadow = true;
        obj.receiveShadow = true;
        const mat = obj.material as THREE.MeshStandardMaterial;
        mat.envMapIntensity = 1.2;
      }
    });

    scene.add(model);
    hideStatus();
  },
  undefined,
  (err) => {
    console.error(err);
    setStatus("failed to load snowman.glb — is it in public/models/?", true);
  }
);

// ---------------------------------------------------------------- loop
renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});

// ---------------------------------------------------------------- resize
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
