-- ============================================================
-- Seed: company_info — Datos estructurados verificados
-- Riopaila Castilla — Módulo 2
--
-- FUENTE: data/knowledge/riopaila_castilla_clean.md
--         (scraping web oficial + LinkedIn + Instagram + SIMEV)
-- ============================================================

truncate table company_info restart identity;

insert into company_info (category, key, value, description) values

-- ============================================================
-- CONTACTO
-- ============================================================
('contacto', 'sitio_web',
 'https://www.riopaila-castilla.com',
 'Sitio web oficial'),

('contacto', 'linea_transparencia_email',
 'riopailacastilla@lineatransparencia.com',
 'Canal ético y de denuncias — disponible 24/7'),

('contacto', 'cumplimiento_email',
 'oficinadecumplimiento@riopaila-castilla.com',
 'Oficina de cumplimiento corporativo'),

('contacto', 'ventas_miel_email',
 'ventasmiel@riopaila-castilla.com',
 'Contacto comercial para ventas de miel'),

('contacto', 'atencion_proveedor_email',
 'atencionalproveedor@riopaila-castilla.com',
 'Centro de Atención al Proveedor (CAP), planta Riopaila'),

-- ============================================================
-- REDES SOCIALES
-- ============================================================
('redes_sociales', 'instagram',
 'https://www.instagram.com/riopailacastilla/',
 'Perfil oficial — @riopailacastilla — 13.3 mil seguidores'),

('redes_sociales', 'linkedin',
 'https://www.linkedin.com/company/riopaila-castilla-s.-a.',
 'Perfil LinkedIn oficial'),

('redes_sociales', 'youtube',
 'https://www.youtube.com/@RiopailaCastilla/videos',
 'Canal oficial de YouTube'),

('redes_sociales', 'facebook',
 'https://www.facebook.com/riopailacastilla/',
 'Página oficial de Facebook'),

-- ============================================================
-- SEDES Y UBICACIONES
-- ============================================================
('sedes', 'domicilio_principal',
 'Carrera 2 No. 1-60, Santiago de Cali, Valle del Cauca',
 'Domicilio social principal (sede Dann Carlton)'),

('sedes', 'oficina_cali',
 'Edificio Belmonte, Cali, Valle del Cauca',
 'Oficinas administrativas en Cali (desde 1956)'),

('sedes', 'planta_riopaila',
 'Corregimiento La Paila, sur del municipio de Zarzal, Valle del Cauca',
 'Planta industrial principal — fundada en 1918'),

('sedes', 'planta_castilla',
 'Pradera, Valle del Cauca',
 'Planta industrial Castilla — fundada en 1945'),

('sedes', 'operaciones_vichada',
 'Santa Rosalía y La Primavera, Vichada (proyecto Veracruz); Puerto López, Meta (proyecto La Conquista)',
 'Operaciones de palma y ganadería en la Altillanura colombiana — desde 2010'),

('sedes', 'presencia_geografica',
 '36 municipios en Valle del Cauca, Cauca y Vichada',
 'Operaciones directas; productos en más de 46 países'),

-- ============================================================
-- DATOS LEGALES
-- ============================================================
('legal', 'nit',
 '900.087.414-4',
 'NIT de Riopaila Castilla S.A.'),

('legal', 'razon_social',
 'Riopaila Castilla S.A.',
 'Razón social vigente desde la fusión de 2007'),

('legal', 'domicilio_legal',
 'Santiago de Cali, Valle del Cauca, Colombia',
 'Domicilio principal de la Sociedad'),

('legal', 'año_fundacion',
 '1918',
 'Inicio como trapiche panelero en hacienda Riopaila, Zarzal, Valle del Cauca'),

('legal', 'año_fusion_actual',
 '2007',
 'Fusión de Riopaila Industrial S.A. y Castilla Industrial S.A. que da origen a Riopaila Castilla S.A.'),

('legal', 'fundador',
 'Doctor Hernando Caicedo',
 'Fundó el Ingenio Riopaila S.A. en 1928 y Central Castilla S.A. en 1945'),

-- ============================================================
-- CIFRAS CLAVE
-- ============================================================
('cifras', 'trabajadores',
 'Más de 3.800 trabajadores directos',
 '94% habitantes de las zonas de operación directa — dato del KB consolidado'),

('cifras', 'aliados_cadena',
 'Más de 2.000 aliados en la cadena de abastecimiento',
 'Incluye 678 familias agricultoras productoras de caña y más de 1.300 proveedores'),

('cifras', 'hogares_con_productos',
 'Más de 15 millones de hogares colombianos',
 'Alcance de productos Riopaila Castilla en Colombia'),

('cifras', 'energia_cogenerada',
 'Energía para más de 110.000 personas',
 'Cogeneración a partir del bagazo de la caña'),

('cifras', 'vehiculos_combustible',
 '440.000 vehículos en promedio',
 'Oxigenación con combustible renovable (etanol) en Colombia'),

('cifras', 'presencia_internacional',
 '46 países',
 'Países a los que llegan los productos de Riopaila Castilla'),

-- ============================================================
-- LÍNEAS DE NEGOCIO
-- ============================================================
('negocio', 'lineas_principales',
 'Azúcar | Energía (cogeneración con bagazo) | Biocombustibles (etanol) | Derivados (miel, melaza, abono orgánico) | Aceite de palma | Ganadería | Servicios agrícolas',
 'Líneas de negocio del grupo agroindustrial'),

('negocio', 'modelo_core',
 'Agroindustrial: cultivo de caña de azúcar + transformación industrial + energía renovable + biocombustibles',
 'Modelo de negocio central'),

('negocio', 'vacantes_empleo',
 'https://www.riopaila-castilla.com — sección "Trabaja con nosotros"',
 'Portal de ofertas laborales — publicadas cada viernes (#ViernesdeVacantes en LinkedIn e Instagram)'),

-- ============================================================
-- SOSTENIBILIDAD E INFORMES
-- ============================================================
('sostenibilidad', 'reporte_gri',
 'Informe de Sostenibilidad y Gestión — estándar GRI desde 2010',
 'También reporta bajo Circulares 012/2022 y 031/2021 de la Superintendencia Financiera de Colombia'),

('sostenibilidad', 'informe_2025_url',
 'https://www.riopaila-castilla.com/wp-content/uploads/2026/03/Informe-RC-Marzo-27-compressed.pdf',
 'Informe de Gestión y Sostenibilidad 2025 — publicado en marzo 2026'),

('sostenibilidad', 'linea_etica',
 'riopailacastilla@lineatransparencia.com',
 'Canal ético externo 24/7 para denuncias y consultas de transparencia'),

-- ============================================================
-- CERTIFICACIONES
-- ============================================================
('certificaciones', 'iso_9001',
 'ISO 9001:2015 — Sistema de Gestión de Calidad (implementada)',
 'Plantas Castilla y Riopaila — primera certificación obtenida en 1999'),

('certificaciones', 'iso_14001',
 'ISO 14001 — Gestión Ambiental',
 'Certificada desde 2006; renovada en planta Castilla en 2008'),

('certificaciones', 'iso_iec_17025',
 'ISO/IEC 17025:2017 — Competencia de laboratorios de ensayo',
 'Laboratorio de alcohol de la destilería, acreditado por ONAC desde 2018'),

('certificaciones', 'gluten_free',
 'Certificación Gluten Free — plantas Castilla y Riopaila',
 NULL),

('certificaciones', 'vegan',
 'Certificación Vegan — plantas Castilla y Riopaila',
 NULL),

('certificaciones', 'non_gmo',
 'Certificación Non-GMO — plantas Castilla y Riopaila',
 NULL),

('certificaciones', 'natural_process',
 'Certificación Natural Process — plantas Castilla y Riopaila',
 NULL),

('certificaciones', 'fsa',
 'Certificación FSA (Farm Sustainability Assessment)',
 'Sostenibilidad en la cadena agrícola'),

-- ============================================================
-- FUNDACIÓN
-- ============================================================
('fundacion', 'nombre',
 'Fundación Caicedo González Riopaila Castilla',
 'Brazo social del grupo — fundada el 29 de noviembre de 1957'),

('fundacion', 'proposito',
 'Motor para el desarrollo integral de los trabajadores y las comunidades de influencia',
 'Opera en zonas rurales de Valle del Cauca, Cauca y Vichada');
