# Propósito

El propósito de la base de datos es almacenar y organizar la información necesaria para una plataforma web de evaluación cualitativa de maestros. La aplicación busca permitir que los estudiantes de la institución educativa puedan expresar su percepción sobre las clases y el desempeño de sus maestros. El objetivo principal no es únicamente asignar una calificación numérica, sino recopilar información que permita identificar aspectos positivos y oportunidades de mejora en el proceso educativo.

La base de datos debe garantizar que las evaluaciones provengan de usuarios pertenecientes a la institución. Para esto, el sistema utiliza el documento de identidad del usuario como identificador para iniciar sesión. De esta manera, se busca reducir la posibilidad de que personas externas a la institución ingresen a la plataforma y registren evaluaciones. Además, cada evaluación debe quedar relacionada con el usuario que la realizó y con el maestro que fue evaluado.

Una de las razones para utilizar una base de datos es que la información de las evaluaciones debe mantenerse organizada y disponible para futuras consultas. Por ejemplo, la institución podría necesitar consultar las evaluaciones recibidas por un determinado maestro o analizar los resultados de una materia específica. Al mantener la información estructurada, la aplicación puede realizar estas consultas sin tener que almacenar repetidamente los mismos datos.

También es importante que la base de datos permita diferenciar correctamente a los usuarios, maestros y evaluaciones. Cada uno representa un elemento diferente dentro del funcionamiento de la página y, por esta razón, se decidió separar la información en distintas entidades relacionadas entre sí.

# Alcance

El alcance de la base de datos comprende principalmente cuatro tipos de información: los usuarios que tienen acceso a la plataforma, los maestros que pueden ser evaluados, las materias relacionadas con los maestros y las evaluaciones realizadas por los usuarios.

La página no tiene como objetivo reemplazar los sistemas académicos de la institución. Tampoco pretende almacenar datos completos de los estudiantes como las notas, asistencia, historial académico o procesos académicos. Su función está enfocada únicamente en las evaluaciones docentes y en la información necesaria para que estas puedan realizarse correctamente.

La base de datos permitirá que un usuario ingrese a la plataforma, identifique al maestro que desea evaluar y registre la información correspondiente a la evaluación. Esta información podrá incluir una calificación y, dependiendo de cómo se implemente la página, otros datos relacionados con la percepción del estudiante sobre la clase.

El alcance también contempla que un maestro pueda estar relacionado con diferentes materias. Esto es importante porque un mismo maestro podría enseñar más de una asignatura y las evaluaciones podrían variar dependiendo de la materia. Por esta razón, incluir la entidad Materia permite organizar mejor la información.

No se busca almacenar información innecesaria. Mantener un alcance limitado ayuda a que el proyecto sea más sencillo de desarrollar y reduce la cantidad de datos que deben ser administrados. Si posteriormente se requieren nuevas funciones, la base de datos podría ampliarse con nuevas entidades.

# Entidades

La entidad principal son los **Usuarios**. Esta entidad almacena la información necesaria para identificar a las personas que pueden utilizar la plataforma. El documento de identidad funciona como identificador del usuario, ya que es un dato que permite diferenciar a una persona de otra dentro de la institución.

Además del documento de identidad, un usuario puede tener información como su nombre y contraseña. La contraseña se utilizará para permitir el acceso a la página. En una implementación real, la contraseña no debería almacenarse directamente como texto, sino de forma segura mediante un mecanismo de hash. Sin embargo, para el modelo inicial se representa como el atributo `password`.

La entidad **Maestro** representa a los profesores que pueden ser evaluados dentro de la plataforma. Cada maestro tiene un identificador propio (`id_maestro`) y un nombre. Se utiliza un identificador independiente porque el nombre de una persona no necesariamente es único. Esto también permite que la información del maestro pueda ser modificada sin tener que cambiar las evaluaciones que ya existen.

La entidad **Evaluacion** representa cada valoración realizada por un usuario sobre un maestro. Esta es una de las entidades centrales del sistema, ya que conecta al usuario que realiza la evaluación con el maestro evaluado. Una evaluación puede almacenar la fecha en que fue realizada y la calificación obtenida.

La entidad **Materia** o **Curso** sirve para identificar la asignatura en la que el estudiante recibe clases del maestro. Esta entidad permite agregar contexto a una evaluación. Por ejemplo, un mismo maestro podría dictar diferentes materias, y el análisis de sus evaluaciones podría necesitar distinguir entre ellas.

Finalmente, la entidad **MaestroMateria** funciona como una tabla intermedia entre Maestro y Materia. Su propósito es representar qué materias dicta cada maestro cuando existe una relación de muchos a muchos.

# Relaciones

La relación principal es entre **Usuario y Evaluacion**. Un usuario puede realizar varias evaluaciones a lo largo del tiempo, pero cada evaluación pertenece a un único usuario. Por lo tanto, la relación es de uno a muchos. Esto permite saber qué usuario realizó una evaluación determinada y también permite consultar todas las evaluaciones realizadas por un usuario.

También existe una relación entre **Maestro y Evaluacion**. Un maestro puede recibir muchas evaluaciones de diferentes usuarios y, en consecuencia, la relación también es de uno a muchos. Cada evaluación debe apuntar mediante una clave foránea al maestro correspondiente.

Entre **Maestro y Materia** puede existir una relación de muchos a muchos. Esto significa que un maestro puede dictar varias materias y una materia puede ser dictada por diferentes maestros. Para representar correctamente esta relación se utiliza la entidad intermedia `MaestroMateria`.

Una evaluación puede estar relacionada con una materia. Esto resulta útil porque permite responder preguntas como cuántas evaluaciones recibió un maestro en una asignatura determinada. También permite realizar análisis separados por materia en lugar de mezclar todas las evaluaciones de un mismo maestro.

Las claves foráneas son importantes en este diseño porque mantienen la integridad referencial. No debería existir una evaluación asociada a un usuario, maestro o materia que no exista previamente en la base de datos. De esta manera se reducen los errores y se mantiene la consistencia de la información.

# Diseño relacional compuesto

El esquema relacional propuesto es el siguiente:

```
Usuario (documento_identidad, nombre, password)

Maestro (id_maestro, nombre)

Materia (id_materia, nombre)

Evaluacion (id_evaluacion, documento_usuario, id_maestro, id_materia, fecha, calificacion)

MaestroMateria (id_maestro, id_materia)

```

En este diseño, `documento_identidad` es la clave primaria de `Usuario`, mientras que `id_maestro`, `id_materia` e `id_evaluacion` son identificadores únicos para sus respectivas entidades.

Las columnas `documento_usuario`, `id_maestro` e `id_materia` de `Evaluacion` funcionan como claves foráneas. `documento_usuario` referencia al usuario que realizó la evaluación, `id_maestro` identifica al maestro evaluado y `id_materia` identifica la materia sobre la cual se realizó la evaluación.

En `MaestroMateria`, la combinación de `id_maestro` e `id_materia` puede funcionar como una clave primaria compuesta. Esto evita que la misma combinación de maestro y materia sea registrada varias veces innecesariamente.

La decisión de dividir la información en estas tablas busca evitar la repetición de datos. Por ejemplo, no sería conveniente guardar el nombre del maestro directamente en cada evaluación. Si un maestro recibe cien evaluaciones, su nombre se repetiría cien veces. En cambio, al utilizar `id_maestro`, el nombre se almacena una sola vez en la tabla `Maestro`.

# Optimizaciones

Para mejorar el rendimiento de la base de datos, las claves primarias deben estar correctamente indexadas. Esto permite encontrar rápidamente un usuario, maestro, materia o evaluación mediante su identificador.

También puede ser conveniente utilizar índices en las claves foráneas de la tabla `Evaluacion`, especialmente en `id_maestro`, `documento_usuario` e `id_materia`. Estas columnas pueden ser utilizadas frecuentemente para realizar consultas. Por ejemplo, cuando la página necesite mostrar todas las evaluaciones de un determinado maestro, el índice sobre `id_maestro` puede ayudar a encontrar los registros de manera más eficiente.

No sería necesario crear una gran cantidad de índices desde el principio. Los índices deben estar relacionados con las consultas que realmente realizará la aplicación, ya que demasiados índices pueden ocupar espacio adicional y hacer más lentas algunas operaciones de inserción o modificación.

Otra optimización importante es evitar almacenar información repetida. En lugar de guardar los nombres completos del usuario y del maestro dentro de cada evaluación, se utilizan sus identificadores. Esto reduce el tamaño de la información almacenada y facilita mantener los datos actualizados.

# Limitaciones

Una de las principales limitaciones del proyecto es que utilizar el documento de identidad como método de inicio de sesión no garantiza completamente que la persona que ingresa sea realmente el propietario de ese documento. Para mejorar la seguridad, la aplicación podría utilizar posteriormente otros mecanismos de autenticación.

Otra limitación está relacionada con la información de las evaluaciones. Una calificación representa la opinión de un estudiante y, por lo tanto, no necesariamente representa de manera objetiva el desempeño real de un maestro. La base de datos únicamente almacena la información proporcionada por los usuarios; no puede determinar si una evaluación es justa o correcta.

También debe considerarse la privacidad. Como cada evaluación está relacionada con el usuario que la realizó, técnicamente es posible identificar quién realizó determinada evaluación. Dependiendo de las decisiones de la institución, podría ser necesario implementar un sistema donde los resultados sean anónimos para los maestros, aunque los administradores puedan mantener la relación entre el usuario y la evaluación para controlar el funcionamiento de la plataforma.

Otra limitación es que el modelo actual no contempla información académica adicional. No se almacenan notas, asistencia, horarios completos ni historial académico de los estudiantes. Esto es intencional, ya que estos datos están fuera del propósito principal de la plataforma.

# Conclusión

El diseño propuesto busca crear una base de datos sencilla, organizada y suficiente para el funcionamiento inicial de la plataforma de evaluación docente. Las entidades principales son Usuario, Maestro, Materia y Evaluacion, mientras que MaestroMateria permite representar la relación entre los maestros y las materias que dictan.

La entidad Evaluacion es el elemento central porque permite conectar a un usuario con un maestro y una materia, además de almacenar la información correspondiente a la valoración realizada. La utilización de claves primarias y foráneas permite mantener relaciones claras entre las diferentes tablas y ayuda a evitar información inconsistente.

La estructura también permite que el proyecto pueda crecer en el futuro. Si la institución necesita agregar nuevas características, como diferentes criterios de evaluación, períodos académicos o tipos de usuario, se pueden incorporar nuevas entidades y relaciones sin tener que modificar completamente el modelo existente. De esta manera, la base de datos mantiene un equilibrio entre las necesidades actuales del proyecto y la posibilidad de ampliarlo posteriormente.