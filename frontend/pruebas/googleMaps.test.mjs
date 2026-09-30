// Corre con `npm test` (node:test + type stripping de Node, sin dependencias
// nuevas: el proyecto no tiene un framework de tests de frontend).
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  construirUrlGoogleMaps,
  origenNavegacionParaParadaActual,
} from "../src/utilidades/googleMaps.ts";

const deposito = { latitud: -32.9, longitud: -68.8 };

function parada(estado, latitud, longitud) {
  return { estado, latitud_snapshot: latitud, longitud_snapshot: longitud };
}

test("sin ubicación, la primera parada sale del depósito", () => {
  const paradas = [parada("en_curso", -32.88, -68.82), parada("pendiente", -32.87, -68.84)];
  assert.deepEqual(origenNavegacionParaParadaActual(deposito, paradas), deposito);
});

test("sin ubicación, una parada posterior sale de la parada anterior", () => {
  const paradas = [parada("completada", -32.88, -68.82), parada("en_curso", -32.87, -68.84)];
  assert.deepEqual(origenNavegacionParaParadaActual(deposito, paradas), {
    latitud: -32.88,
    longitud: -68.82,
  });
});

test("con ubicación, la posición actual es el origen", () => {
  const paradas = [parada("completada", -32.88, -68.82), parada("en_curso", -32.87, -68.84)];
  const ubicacion = { latitud: -32.86, longitud: -68.85 };
  assert.deepEqual(origenNavegacionParaParadaActual(deposito, paradas, ubicacion), ubicacion);
});

test("una ubicación null cae al origen del tramo", () => {
  const paradas = [parada("en_curso", -32.88, -68.82)];
  assert.deepEqual(origenNavegacionParaParadaActual(deposito, paradas, null), deposito);
});

test("sin parada en curso no hay origen, ni siquiera con ubicación", () => {
  const paradas = [parada("completada", -32.88, -68.82)];
  const ubicacion = { latitud: -32.86, longitud: -68.85 };
  assert.equal(origenNavegacionParaParadaActual(deposito, paradas, ubicacion), null);
});

test("el enlace de Google Maps usa el origen y el destino indicados", () => {
  const url = construirUrlGoogleMaps(
    { latitud: -32.86, longitud: -68.85 },
    { latitud: -32.87, longitud: -68.84 },
  );
  assert.ok(url.includes("origin=-32.86,-68.85"));
  assert.ok(url.includes("destination=-32.87,-68.84"));
});
