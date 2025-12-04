cd backend

python -m venv venv

venv\Scripts\activate

pip freeze > requirements.txt

pip install -r requirements.txt

cd backend

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

http://127.0.0.1:8000/docs

http://localhost:8000/public/index.html
http://localhost:8000/public/conductores.html

SELECT * FROM usuarios;
SELECT * FROM conductores;
SELECT * FROM productos;
SELECT * FROM pedidos;
SELECT * FROM detalles_pedido;
SELECT * FROM pagos;
SELECT * FROM historial_estados;
SELECT * FROM notificaciones;
SELECT * FROM ubicaciones;
