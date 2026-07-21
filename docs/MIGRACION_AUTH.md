# Migración de `usuarios` a Supabase Auth

Procedimiento para retirar la tabla `usuarios` con bcrypt propio. Se ejecuta en
la Fase 7, junto con el resto de la migración de esquema.

**Nada de esto se ha ejecutado.** Es un guion a seguir, no un script probado.

## Por qué

La tabla actual (`data.py:52`) guarda `username`, `password_hash` y `tipo`, y
obliga a mantener a mano el hasheo y el alta. No tiene recuperación de
contraseña, no permite invitar a nadie por correo —que es lo que el panel de
Registradores necesita— y no es visible desde dentro de Postgres, así que no se
pueden escribir políticas RLS contra ella.

## Punto a favor: los hashes se conservan

Supabase Auth guarda `encrypted_password` en formato bcrypt, el mismo que usa
`bcrypt.checkpw` hoy. Los usuarios existentes **no tienen que cambiar su
contraseña**: el hash se importa tal cual.

Esto solo vale si los hashes actuales son bcrypt con prefijo `$2a$`/`$2b$`.
Conviene comprobarlo antes de nada:

```sql
select substring(password_hash from 1 for 4) as prefijo, count(*)
from usuarios group by 1;
```

Si aparece cualquier otro prefijo, esas cuentas hay que darlas de alta por
invitación y que fijen contraseña nueva.

## Pasos

1. **Respaldo.** Volcado completo antes de tocar nada.

2. **Correo por usuario.** `auth.users` identifica por correo, y la tabla actual
   solo tiene `username`. Los que no tengan correo hay que resolverlos a mano;
   `ServicioDeRegistradores.otorgar_por_usuario` existe precisamente para poder
   concederles permiso sin él.

3. **Importar.** Por cada fila con hash bcrypt válido, insertar en `auth.users`
   con `encrypted_password` copiado y `email_confirmed_at` puesto, para que no se
   les exija confirmar un correo que ya usaban.

4. **Traducir los roles.** El `tipo` actual se convierte en filas de
   `concesiones`:

   | `usuarios.tipo` | Concesión |
   |---|---|
   | administrador | `(usuario, NULL, 'admin')` |
   | profesor | `(usuario, <competición>, 'registrador')` por cada competición que gestione |
   | cualquier otro | ninguna: visitante es lo que se es sin concesión |

   El profesor es el caso que **no se puede automatizar**: hoy su permiso es
   global y en el modelo nuevo tiene alcance. Hay que decidir competición por
   competición, y ese reparto es una decisión del Admin, no del script.

5. **Verificar antes de borrar.** Que cada usuario activo tenga su fila en
   `auth.users` y las concesiones que le tocan. La tabla `usuarios` se conserva
   hasta que se confirme que nadie ha perdido el acceso.

6. **Retirar.** `verificar_login` y la tabla `usuarios` salen del código en la
   Fase 8, cuando la interfaz pase a autenticarse contra Supabase Auth.

## Reporte de conflictos

Como en el backfill de enfrentamientos, las filas irresolubles —sin correo, con
hash de formato desconocido, con correo duplicado— **se emiten en un reporte para
resolución manual**. No se descartan en silencio.
