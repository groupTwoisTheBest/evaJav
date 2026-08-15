# Propósito

El propósito de la base de datos es almacenar y organizar la información necesaria para una plataforma web de evaluación cualitativa de maestros. La aplicación busca permitir que los estudiantes de la institución educativa puedan expresar su percepción sobre las clases y el desempeño de sus maestros. El objetivo principal no es únicamente asignar una calificación numérica, sino recopilar información que permita identificar aspectos positivos y oportunidades de mejora en el proceso educativo.

La base de datos debe garantizar que las evaluaciones provengan de usuarios pertenecientes a la institución. Para esto, el sistema utiliza el documento de identidad del usuario como identificador para iniciar sesión. De esta manera, se busca reducir la posibilidad de que personas externas a la institución ingresen a la plataforma y registren evaluaciones.

Además, el sistema contará con un usuario de tipo **Administrador**, cuya función será gestionar y consultar la información relacionada con las evaluaciones docentes. El administrador podrá revisar los resultados generales y consultar los promedios obtenidos por los maestros, teniendo en cuenta diferentes criterios como el grado y el grupo de los estudiantes que realizaron las evaluaciones.

Una característica importante de la plataforma es que las evaluaciones serán **anónimas para los resultados mostrados**. Esto significa que los maestros no podrán conocer qué estudiante realizó una determinada evaluación. En lugar de mostrar evaluaciones individuales, la plataforma presentará principalmente los **promedios obtenidos por cada maestro**, evitando exponer la identidad de los estudiantes.

La información de las evaluaciones debe mantenerse organizada y disponible para futuras consultas. Por ejemplo, la institución podría necesitar consultar el promedio de las evaluaciones recibidas por un determinado maestro o analizar los resultados de un maestro según un grado o grupo específico. Al mantener la información estructurada, la aplicación puede realizar estas consultas sin tener que almacenar repetidamente los mismos datos.

También es importante que la base de datos permita diferenciar correctamente a los usuarios, administradores, maestros, materias y evaluaciones. Cada uno representa un elemento diferente dentro del funcionamiento de la página y, por esta razón, se decidió separar la información en distintas entidades relacionadas entre sí.

# Alcance

El alcance de la base de datos comprende principalmente cinco tipos de información: los usuarios que tienen acceso a la plataforma, los administradores encargados de consultar y gestionar los resultados, los maestros que pueden ser evaluados, las materias relacionadas con los maestros y las evaluaciones realizadas por los usuarios.

La página no tiene como objetivo reemplazar los sistemas académicos de la institución. Tampoco pretende almacenar datos completos de los estudiantes como las notas, asistencia, historial académico o procesos académicos. Su función está enfocada principalmente en las evaluaciones docentes y en la información necesaria para que estas puedan realizarse correctamente.

La base de datos permitirá que un estudiante ingrese a la plataforma, identifique al maestro y la materia que desea evaluar y registre la información correspondiente. Esta información podrá incluir una calificación y, dependiendo de cómo se implemente la página, otros datos relacionados con la percepción del estudiante sobre la clase.

Los usuarios estudiantes también estarán asociados a un **grado y un grupo**, ya que esta información será necesaria para que el administrador pueda analizar los resultados de las evaluaciones de acuerdo con estos criterios.

El sistema contará además con un **Administrador**, quien tendrá permisos diferentes a los de los estudiantes. Su función principal será consultar los resultados de las evaluaciones y visualizar los promedios de los maestros. El administrador podrá realizar consultas generales o filtradas por maestro, materia, grado y grupo.

El alcance contempla que un maestro pueda estar relacionado con diferentes materias. Esto es importante porque un mismo maestro podría enseñar más de una asignatura y las evaluaciones podrían variar dependiendo de la materia. Por esta razón, incluir la entidad Materia permite organizar mejor la información.

Las evaluaciones serán anónimas desde el punto de vista de los resultados mostrados. Los estudiantes no podrán consultar quién realizó una evaluación y los maestros tampoco podrán identificar al estudiante que realizó una determinada valoración. La información presentada estará basada en resultados agregados, principalmente mediante promedios.

No se busca almacenar información innecesaria. Mantener un alcance limitado ayuda a que el proyecto sea más sencillo de desarrollar y reduce la cantidad de datos que deben ser administrados. Si posteriormente se requieren nuevas funciones, la base de datos podría ampliarse con nuevas entidades.

# Entidades

La entidad principal son los **Usuarios**. Esta entidad almacena la información necesaria para identificar a los estudiantes que pueden utilizar la plataforma. El documento de identidad funciona como identificador del usuario, ya que es un dato que permite diferenciar a una persona de otra dentro de la institución.

Además del documento de identidad, un usuario puede tener información como su nombre, contraseña, grado y grupo. El grado y el grupo son importantes porque permiten clasificar a los estudiantes y posteriormente analizar los resultados de las evaluaciones según estos criterios.

La contraseña se utilizará para permitir el acceso a la página. En una implementación real, la contraseña no debería almacenarse directamente como texto, sino de forma segura mediante un mecanismo de hash. Sin embargo, para el modelo inicial se representa como el atributo `password`.

La entidad **Administrador** representa a los usuarios que tienen permisos especiales dentro de la plataforma. Un administrador podrá consultar los resultados de las evaluaciones, revisar los promedios obtenidos por los maestros y realizar análisis según maestro, materia, grado y grupo. A diferencia de un estudiante, el administrador tendrá acceso a las herramientas de consulta y gestión de resultados.

La entidad **Maestro** representa a los profesores que pueden ser evaluados dentro de la plataforma. Cada maestro tiene un identificador propio (`id_maestro`) y un nombre. Se utiliza un identificador independiente porque el nombre de una persona no necesariamente es único. Esto también permite que la información del maestro pueda ser modificada sin tener que cambiar las evaluaciones que ya existen.

La entidad **Evaluacion** representa cada valoración realizada por un usuario sobre un maestro. Esta es una de las entidades centrales del sistema, ya que conecta al estudiante con el maestro y la materia evaluada. Una evaluación puede almacenar la fecha en que fue realizada y la calificación obtenida.

Aunque la evaluación pueda estar relacionada internamente con el usuario que la realizó, esta información no deberá mostrarse en los resultados de la plataforma. De esta manera, se puede mantener la organización e integridad de los datos sin revelar la identidad del estudiante en los resultados visibles.

La entidad **Materia** o **Curso** sirve para identificar la asignatura en la que el estudiante recibe clases del maestro. Esta entidad permite agregar contexto a una evaluación. Por ejemplo, un mismo maestro podría dictar diferentes materias, y el análisis de sus evaluaciones podría necesitar distinguir entre ellas.

Finalmente, la entidad **MaestroMateria** funciona como una tabla intermedia entre Maestro y Materia. Su propósito es representar qué materias dicta cada maestro cuando existe una relación de muchos a muchos.

# Relaciones

La relación principal es entre **Usuario y Evaluacion**. Un usuario puede realizar varias evaluaciones a lo largo del tiempo, pero cada evaluación pertenece a un único usuario. Por lo tanto, la relación es de uno a muchos.

Sin embargo, debido a que las evaluaciones son anónimas, la relación entre Usuario y Evaluacion no debe utilizarse para mostrar públicamente la identidad del estudiante. La información del usuario puede mantenerse internamente para garantizar que solamente estudiantes registrados puedan realizar evaluaciones y para mantener la integridad del sistema, mientras que los resultados presentados estarán agrupados y serán anónimos.

También existe una relación entre **Maestro y Evaluacion**. Un maestro puede recibir muchas evaluaciones de diferentes usuarios y, en consecuencia, la relación es de uno a muchos. Cada evaluación debe apuntar mediante una clave foránea al maestro correspondiente.

Entre **Maestro y Materia** existe una relación de muchos a muchos. Esto significa que un maestro puede dictar varias materias y una materia puede ser dictada por diferentes maestros. Para representar correctamente esta relación se utiliza la entidad intermedia `MaestroMateria`.

Una evaluación también está relacionada con una materia. Esto resulta útil porque permite responder preguntas como cuántas evaluaciones recibió un maestro en una asignatura determinada. También permite realizar análisis separados por materia en lugar de mezclar todas las evaluaciones de un mismo maestro.

Los **Usuarios** también se relacionan con un grado y un grupo. Esta información permitirá clasificar las evaluaciones realizadas por los estudiantes y proporcionar al administrador resultados como el promedio de un maestro en determinado grado o grupo.

El **Administrador** tendrá acceso a las evaluaciones y a los resultados agregados, pero no deberá visualizar la identidad del estudiante asociada a una evaluación individual. Su función será consultar información estadística y promedios para facilitar el análisis del desempeño docente.

Las claves foráneas son importantes en este diseño porque mantienen la integridad referencial. No debería existir una evaluación asociada a un usuario, maestro o materia que no exista previamente en la base de datos. De esta manera se reducen los errores y se mantiene la consistencia de la información.

# Diseño relacional compuesto

El esquema relacional propuesto es el siguiente:

```text
Usuario (documento_identidad, nombre, password, grado, grupo)

Administrador (id_administrador, nombre, password)

Maestro (id_maestro, nombre)

Materia (id_materia, nombre)

Evaluacion (id_evaluacion, documento_usuario, id_maestro, id_materia, fecha, calificacion)

MaestroMateria (id_maestro, id_materia)
```

En este diseño, `documento_identidad` es la clave primaria de `Usuario`, mientras que `id_administrador`, `id_maestro`, `id_materia` e `id_evaluacion` son identificadores únicos para sus respectivas entidades.

Las columnas `documento_usuario`, `id_maestro` e `id_materia` de `Evaluacion` funcionan como claves foráneas. `documento_usuario` referencia al usuario que realizó la evaluación, `id_maestro` identifica al maestro evaluado y `id_materia` identifica la materia sobre la cual se realizó la evaluación.

En `MaestroMateria`, la combinación de `id_maestro` e `id_materia` puede funcionar como una clave primaria compuesta. Esto evita que la misma combinación de maestro y materia sea registrada varias veces innecesariamente.

Los atributos `grado` y `grupo` de `Usuario` permiten clasificar a los estudiantes según su ubicación académica dentro de la institución. Esta información puede utilizarse para generar consultas y promedios sin necesidad de revelar la identidad de los estudiantes.

La información de `Evaluacion` se utilizará principalmente para generar resultados agregados. Por ejemplo, el sistema podría calcular el promedio de las calificaciones recibidas por un maestro, el promedio de un maestro en una materia específica o el promedio obtenido por un maestro según determinado grado y grupo.

La decisión de dividir la información en estas tablas busca evitar la repetición de datos. Por ejemplo, no sería conveniente guardar el nombre del maestro directamente en cada evaluación. Si un maestro recibe cien evaluaciones, su nombre se repetiría cien veces. En cambio, al utilizar `id_maestro`, el nombre se almacena una sola vez en la tabla `Maestro`.

# Anonimato y visualización de resultados

Uno de los aspectos principales del funcionamiento de la plataforma es el **anonimato de las evaluaciones**. El objetivo es que los estudiantes puedan expresar su opinión sobre los maestros sin temor a que su identidad sea expuesta.

Por esta razón, la plataforma no deberá mostrar evaluaciones individuales asociadas al nombre o documento de identidad de un estudiante. Los resultados que podrán consultar los administradores estarán principalmente representados mediante **promedios y datos agrupados**.

Por ejemplo, en lugar de mostrar:

```text
Estudiante: 123456789
Calificación: 4.5
Maestro: Juan Pérez
```

el sistema mostrará información similar a:

```text
Maestro: Juan Pérez
Materia: Matemáticas
Grado: 10°
Grupo: A
Promedio: 4.5
```

De esta manera, el administrador puede analizar el desempeño percibido de los maestros sin necesidad de conocer qué estudiante realizó cada evaluación.

El nivel de agrupación también debe tenerse en cuenta para proteger el anonimato. Si un grupo tiene muy pocos estudiantes y se muestra un resultado demasiado específico, podría ser posible inferir quién realizó una evaluación. Por esta razón, la aplicación podría establecer posteriormente una cantidad mínima de respuestas necesarias antes de mostrar un promedio.

# Funciones del Administrador

El **Administrador** tendrá un papel diferente al de los estudiantes. Mientras los estudiantes utilizan la plataforma principalmente para realizar evaluaciones, el administrador tendrá permisos para consultar y analizar los resultados.

Entre las principales funciones del administrador se encuentran:

* Consultar los promedios obtenidos por cada maestro.
* Consultar los resultados de un maestro en una materia determinada.
* Filtrar resultados por grado.
* Filtrar resultados por grupo.
* Analizar los promedios obtenidos por diferentes maestros.
* Consultar información general de las evaluaciones realizadas.
* Revisar los resultados sin acceder a la identidad de los estudiantes que realizaron las evaluaciones.

La información presentada al administrador debe estar orientada al análisis general del desempeño docente y no a identificar estudiantes específicos.

# Optimizaciones

Para mejorar el rendimiento de la base de datos, las claves primarias deben estar correctamente indexadas. Esto permite encontrar rápidamente un usuario, administrador, maestro, materia o evaluación mediante su identificador.

También puede ser conveniente utilizar índices en las claves foráneas de la tabla `Evaluacion`, especialmente en `id_maestro`, `documento_usuario` e `id_materia`. Estas columnas pueden ser utilizadas frecuentemente para realizar consultas.

También podrían crearse índices sobre `grado` y `grupo` de la tabla `Usuario`, especialmente si el sistema realizará consultas frecuentes para analizar los resultados por estos criterios.

Otra optimización importante consiste en evitar almacenar información repetida. En lugar de guardar los nombres completos del usuario y del maestro dentro de cada evaluación, se utilizan sus identificadores. Esto reduce el tamaño de la información almacenada y facilita mantener los datos actualizados.

Los promedios también podrían calcularse mediante consultas cuando sean necesarios o, si el volumen de información aumenta considerablemente, podrían implementarse mecanismos de almacenamiento de resultados agregados para mejorar el rendimiento.

No sería necesario crear una gran cantidad de índices desde el principio. Los índices deben estar relacionados con las consultas que realmente realizará la aplicación, ya que demasiados índices pueden ocupar espacio adicional y hacer más lentas algunas operaciones de inserción o modificación.

# Limitaciones

Una de las principales limitaciones del proyecto es que utilizar el documento de identidad como método de inicio de sesión no garantiza completamente que la persona que ingresa sea realmente el propietario de ese documento. Para mejorar la seguridad, la aplicación podría utilizar posteriormente otros mecanismos de autenticación.

Otra limitación está relacionada con la información de las evaluaciones. Una calificación representa la opinión de un estudiante y, por lo tanto, no necesariamente representa de manera objetiva el desempeño real de un maestro. La base de datos únicamente almacena la información proporcionada por los usuarios; no puede determinar si una evaluación es justa o correcta.

El anonimato también presenta una consideración importante. Aunque los resultados mostrados sean anónimos, el sistema puede mantener internamente una relación entre el usuario y la evaluación con el objetivo de controlar el acceso y mantener la integridad de la plataforma. Por esta razón, debe establecerse claramente qué usuarios tienen permiso para acceder a esa información y bajo qué condiciones.

En ningún caso los maestros deberían tener acceso a la relación entre una evaluación y el estudiante que la realizó. Los resultados que se les presenten deberán ser agregados y basados en promedios.

Otra limitación está relacionada con los grupos pequeños. Si se muestra un promedio correspondiente a un grupo con muy pocos estudiantes, podría existir el riesgo de identificar indirectamente quién realizó una determinada evaluación. Para reducir este riesgo, la aplicación podría establecer un número mínimo de respuestas antes de mostrar determinados resultados.

También debe considerarse la privacidad y seguridad de los datos. Aunque las evaluaciones sean anónimas en la interfaz, la información almacenada debe protegerse mediante controles de acceso adecuados, especialmente porque los administradores tienen acceso a información general de la plataforma.

Otra limitación es que el modelo actual no contempla información académica adicional. No se almacenan notas, asistencia, horarios completos ni historial académico de los estudiantes. Esto es intencional, ya que estos datos están fuera del propósito principal de la plataforma.

# Conclusión

El diseño propuesto busca crear una base de datos sencilla, organizada y suficiente para el funcionamiento inicial de la plataforma de evaluación docente. Las entidades principales son `Usuario`, `Administrador`, `Maestro`, `Materia` y `Evaluacion`, mientras que `MaestroMateria` permite representar la relación entre los maestros y las materias que dictan.

La entidad `Evaluacion` es el elemento central porque permite relacionar un usuario con un maestro y una materia, además de almacenar la información correspondiente a la valoración realizada. Sin embargo, debido a que las evaluaciones son anónimas, la identidad del estudiante no será mostrada en los resultados. La plataforma utilizará principalmente información agregada y promedios.

El administrador tendrá un papel fundamental en el análisis de la información. Podrá consultar los promedios de las evaluaciones docentes y analizarlos según diferentes criterios, como maestro, materia, grado y grupo. Esto permitirá que la institución tenga una visión general de la percepción de los estudiantes sobre el proceso educativo sin exponer la identidad de quienes realizaron las evaluaciones.

La utilización de claves primarias y foráneas permite mantener relaciones claras entre las diferentes tablas y ayuda a evitar información inconsistente. Además, la separación de las entidades evita la duplicación innecesaria de datos y facilita el crecimiento futuro del proyecto.

La estructura también permite incorporar nuevas características posteriormente, como diferentes criterios de evaluación, períodos académicos, estadísticas más avanzadas o diferentes niveles de permisos para los administradores. De esta manera, la base de datos mantiene un equilibrio entre las necesidades actuales de la plataforma, la protección del anonimato de los estudiantes y la posibilidad de ampliar el sistema en el futuro.