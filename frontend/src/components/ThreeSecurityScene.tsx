import { useEffect, useRef } from "react";
import * as THREE from "three";

export function ThreeSecurityScene() {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    mount.appendChild(renderer.domElement);

    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(4.8, 4.2, 6.8);
    camera.lookAt(0, 0, 0);

    scene.add(new THREE.AmbientLight(0xf7f8f4, 1.7));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(4, 8, 5);
    scene.add(keyLight);
    const rimLight = new THREE.PointLight(0x4f8f6b, 5, 10);
    rimLight.position.set(-3, 2.5, 3);
    scene.add(rimLight);

    const root = new THREE.Group();
    root.rotation.x = -0.42;
    scene.add(root);

    const grid = new THREE.GridHelper(7, 18, 0x7c8b6d, 0xd8ded0);
    grid.position.y = -0.02;
    root.add(grid);

    const base = new THREE.Mesh(
      new THREE.BoxGeometry(5.6, 0.08, 3.5),
      new THREE.MeshStandardMaterial({ color: 0xf7f8f4, roughness: 0.72, metalness: 0.08 })
    );
    base.position.y = -0.08;
    root.add(base);

    const zoneMaterial = new THREE.MeshBasicMaterial({
      color: 0x5e6b4f,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide
    });
    const zone = new THREE.Mesh(new THREE.RingGeometry(0.88, 1.02, 72), zoneMaterial);
    zone.rotation.x = -Math.PI / 2;
    zone.position.set(0.75, 0.02, -0.35);
    root.add(zone);

    const alertMaterial = new THREE.MeshBasicMaterial({
      color: 0x16a34a,
      transparent: true,
      opacity: 0.28,
      side: THREE.DoubleSide
    });
    const alertSweep = new THREE.Mesh(new THREE.CircleGeometry(1.15, 72, 0, Math.PI / 2.6), alertMaterial);
    alertSweep.rotation.x = -Math.PI / 2;
    alertSweep.position.set(-1.25, 0.04, 0.42);
    root.add(alertSweep);

    const buildingMaterial = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.58, metalness: 0.14 });
    const accentMaterial = new THREE.MeshStandardMaterial({ color: 0x8a735a, roughness: 0.48, metalness: 0.22 });
    const towerMaterial = new THREE.MeshStandardMaterial({ color: 0x5e6b4f, roughness: 0.38, metalness: 0.34 });
    const glowMaterial = new THREE.MeshBasicMaterial({ color: 0x22c55e });

    [
      [-1.6, 0.35, -0.75, 0.75],
      [-0.55, 0.55, 0.75, 1.15],
      [1.45, 0.45, 0.82, 0.95],
      [1.85, 0.28, -0.72, 0.56]
    ].forEach(([x, height, z, width], index) => {
      const block = new THREE.Mesh(new THREE.BoxGeometry(width, height, 0.72), index === 1 ? accentMaterial : buildingMaterial);
      block.position.set(x, height / 2, z);
      root.add(block);
    });

    const towers: THREE.Mesh[] = [];
    [
      [-2.25, -1.25],
      [2.35, -1.18],
      [-2.25, 1.25],
      [2.35, 1.18]
    ].forEach(([x, z]) => {
      const tower = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.12, 0.78, 18), towerMaterial);
      tower.position.set(x, 0.39, z);
      root.add(tower);
      towers.push(tower);

      const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.13, 24, 16), glowMaterial);
      beacon.position.set(x, 0.86, z);
      root.add(beacon);
    });

    const lineMaterial = new THREE.LineBasicMaterial({ color: 0x15803d, transparent: true, opacity: 0.55 });
    const perimeterPoints = [
      new THREE.Vector3(-2.55, 0.07, -1.48),
      new THREE.Vector3(2.65, 0.07, -1.48),
      new THREE.Vector3(2.65, 0.07, 1.48),
      new THREE.Vector3(-2.55, 0.07, 1.48),
      new THREE.Vector3(-2.55, 0.07, -1.48)
    ];
    root.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(perimeterPoints), lineMaterial));

    const scanner = new THREE.Mesh(
      new THREE.BoxGeometry(0.04, 0.035, 3.1),
      new THREE.MeshBasicMaterial({ color: 0x22c55e, transparent: true, opacity: 0.7 })
    );
    scanner.position.y = 0.08;
    root.add(scanner);

    const particles = new THREE.Points(
      new THREE.BufferGeometry().setFromPoints(
        Array.from({ length: 90 }, () => new THREE.Vector3((Math.random() - 0.5) * 6, Math.random() * 1.9 + 0.2, (Math.random() - 0.5) * 3.5))
      ),
      new THREE.PointsMaterial({ color: 0x5e6b4f, size: 0.026, transparent: true, opacity: 0.42 })
    );
    root.add(particles);

    const resize = () => {
      const { width, height } = mount.getBoundingClientRect();
      renderer.setSize(Math.max(1, width), Math.max(1, height), false);
      camera.aspect = Math.max(1, width) / Math.max(1, height);
      camera.updateProjectionMatrix();
    };

    let frame = 0;
    let animationId = 0;
    const clock = new THREE.Clock();
    const animate = () => {
      const elapsed = clock.getElapsedTime();
      root.rotation.z = Math.sin(elapsed * 0.28) * 0.08;
      zone.scale.setScalar(1 + Math.sin(elapsed * 2.6) * 0.08);
      alertSweep.rotation.z = elapsed * 1.35;
      scanner.position.x = Math.sin(elapsed * 1.2) * 2.45;
      particles.rotation.y = elapsed * 0.08;
      towers.forEach((tower, index) => {
        tower.rotation.y = elapsed * 0.7 + index;
      });
      renderer.render(scene, camera);
      frame += 1;
      mount.dataset.frames = String(frame);
      animationId = window.requestAnimationFrame(animate);
    };

    resize();
    animate();
    window.addEventListener("resize", resize);

    return () => {
      window.cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
      mount.removeChild(renderer.domElement);
      renderer.dispose();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Points || object instanceof THREE.Line) {
          object.geometry.dispose();
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        }
      });
    };
  }, []);

  return <div ref={mountRef} className="h-full min-h-[220px] w-full" aria-label="Animated 3D facility monitoring scene" />;
}
