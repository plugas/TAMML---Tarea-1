import requests
import json


class ScraperInstagramEstable:

    def __init__(self):
        self.username = "riopailacastilla"
        self.url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "X-IG-App-ID": "936619743392459"
        }

        self.resultados = []

    # ==============================
    # 📸 EXTRAER POSTS (JSON)
    # ==============================
    def scrapear_instagram(self):
        print("\n📸 Extrayendo Instagram (modo ESTABLE)...\n")

        res = requests.get(self.url, headers=self.headers)

        if res.status_code != 200:
            print("❌ Error al acceder a Instagram")
            return

        data = res.json()

        user = data["data"]["user"]

        # 👤 PERFIL
        perfil = {
            "usuario": user["username"],
            "nombre": user["full_name"],
            "seguidores": user["edge_followed_by"]["count"],
            "seguidos": user["edge_follow"]["count"],
            "posts": user["edge_owner_to_timeline_media"]["count"],
            "bio": user["biography"]
        }

        self.resultados.append({
            "tipo": "perfil",
            "data": perfil
        })

        print("👤 PERFIL cargado")

        # 📸 POSTS
        edges = user["edge_owner_to_timeline_media"]["edges"]

        for i, edge in enumerate(edges):

            node = edge["node"]

            texto = ""
            if node["edge_media_to_caption"]["edges"]:
                texto = node["edge_media_to_caption"]["edges"][0]["node"]["text"]

            likes = node["edge_liked_by"]["count"]
            comentarios = node["edge_media_to_comment"]["count"]
            url_post = f"https://www.instagram.com/p/{node['shortcode']}/"

            self.resultados.append({
                "tipo": "post",
                "texto": texto,
                "likes": likes,
                "comentarios": comentarios,
                "url": url_post
            })

            print(f"✔ Post {i+1}")

    # ==============================
    # 💾 GUARDAR
    # ==============================
    def guardar(self):
        print("\n💾 Guardando resultados...\n")

        with open("C:\\Users\\mrplu\\Downloads\\instagram_estable.txt", "w", encoding="utf-8") as f:

            for item in self.resultados:

                f.write("\n" + "="*70 + "\n")

                if item["tipo"] == "perfil":
                    p = item["data"]

                    f.write("📌 PERFIL\n\n")
                    f.write(f"Usuario: {p['usuario']}\n")
                    f.write(f"Nombre: {p['nombre']}\n")
                    f.write(f"Seguidores: {p['seguidores']}\n")
                    f.write(f"Seguidos: {p['seguidos']}\n")
                    f.write(f"Posts: {p['posts']}\n")
                    f.write(f"Bio: {p['bio']}\n")

                else:
                    f.write("📌 POST\n\n")
                    f.write(f"📝 {item['texto']}\n\n")
                    f.write(f"❤️ Likes: {item['likes']}\n")
                    f.write(f"💬 Comentarios: {item['comentarios']}\n")
                    f.write(f"🔗 {item['url']}\n")

        print("✅ Archivo generado: instagram_estable.txt")

    # ==============================
    # 🚀 EJECUCIÓN
    # ==============================
    def ejecutar(self):
        self.scrapear_instagram()
        self.guardar()


# ==============================
# ▶️ MAIN
# ==============================
if __name__ == "__main__":
    scraper = ScraperInstagramEstable()
    scraper.ejecutar()