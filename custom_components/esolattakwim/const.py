"""Constants for the eSolat Takwim Malaysia integration."""
from datetime import timedelta
from zoneinfo import ZoneInfo

DOMAIN = "esolattakwim"
SCAN_INTERVAL = timedelta(days=1)
TIMEZONE = ZoneInfo("Asia/Kuala_Lumpur")

# API endpoints
ISLAMIC_EVENTS_API = "https://www.e-solat.gov.my/index.php?r=esolatApi/islamicevent&type=all"
PRAYER_TIMES_API = "https://www.e-solat.gov.my/index.php?r=esolatApi/takwimsolat&period=duration&zone={zone}"

# Prayer names mapping
PRAYER_NAMES = {
    "imsak": "Imsak",
    "fajr": "Fajr",
    "syuruk": "Syuruk",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha"
}

HIJRI_MONTHS = {
    "01": "Muharram",
    "02": "Safar",
    "03": "Rabi'ul Awwal",
    "04": "Rabi'ul Akhir",
    "05": "Jamadil Awwal",
    "06": "Jamadil Akhir",
    "07": "Rejab",
    "08": "Sha'aban",
    "09": "Ramadhan",
    "10": "Syawal",
    "11": "Zulkaedah",
    "12": "Zulhijjah"
}

# Zone codes and names
ZONES = {
    "jhr01": "JHR01 - Pulau Aur dan Pulau Pemanggil",
    "jhr02": "JHR02 - Johor Bahru, Kota Tinggi, Mersing, Kulai",
    "jhr03": "JHR03 - Kluang, Pontian",
    "jhr04": "JHR04 - Batu Pahat, Muar, Segamat, Gemas Johor, Tangkak",
    "kdh01": "KDH01 - Kota Setar, Kubang Pasu, Pokok Sena (Daerah Kecil)",
    "kdh02": "KDH02 - Kuala Muda, Yan, Pendang",
    "kdh03": "KDH03 - Padang Terap, Sik",
    "kdh04": "KDH04 - Baling",
    "kdh05": "KDH05 - Bandar Baharu, Kulim",
    "kdh06": "KDH06 - Langkawi",
    "kdh07": "KDH07 - Puncak Gunung Jerai",
    "ktn01": "KTN01 - Bachok, Kota Bharu, Machang, Pasir Mas, Pasir Puteh, Tanah Merah, Tumpat, Kuala Krai, Mukim Chiku",
    "ktn02": "KTN02 - Gua Musang (Daerah Galas Dan Bertam), Jeli, Jajahan Kecil Lojing",
    "mlk01": "MLK01 - SELURUH NEGERI MELAKA",
    "ngs01": "NGS01 - Tampin, Jempol",
    "ngs02": "NGS02 - Jelebu, Kuala Pilah, Rembau",
    "ngs03": "NGS03 - Port Dickson, Seremban",
    "phg01": "PHG01 - Pulau Tioman",
    "phg02": "PHG02 - Kuantan, Pekan, Muadzam Shah",
    "phg03": "PHG03 - Jerantut, Temerloh, Maran, Bera, Chenor, Jengka",
    "phg04": "PHG04 - Bentong, Lipis, Raub",
    "phg05": "PHG05 - Genting Sempah, Janda Baik, Bukit Tinggi",
    "phg06": "PHG06 - Cameron Highlands, Genting Higlands, Bukit Fraser",
    "phg07": "PHG07 - Zon Khas Daerah Rompin, (Mukim Rompin, Mukim Endau, Mukim Pontian)",
    "pls01": "PLS01 - Kangar, Padang Besar, Arau",
    "png01": "PNG01 - Seluruh Negeri Pulau Pinang",
    "prk01": "PRK01 - Tapah, Slim River, Tanjung Malim",
    "prk02": "PRK02 - Kuala Kangsar, Sg. Siput , Ipoh, Batu Gajah, Kampar",
    "prk03": "PRK03 - Lenggong, Pengkalan Hulu, Grik",
    "prk04": "PRK04 - Temengor, Belum",
    "prk05": "PRK05 - Kg Gajah, Teluk Intan, Bagan Datuk, Seri Iskandar, Beruas, Parit, Lumut, Sitiawan, Pulau Pangkor",
    "prk06": "PRK06 - Selama, Taiping, Bagan Serai, Parit Buntar",
    "prk07": "PRK07 - Bukit Larut",
    "sbh01": "SBH01 - Bahagian Sandakan (Timur), Bukit Garam, Semawang, Temanggong, Tambisan, Bandar Sandakan, Sukau",
    "sbh02": "SBH02 - Beluran, Telupid, Pinangah, Terusan, Kuamut, Bahagian Sandakan (Barat)",
    "sbh03": "SBH03 - Lahad Datu, Silabukan, Kunak, Sahabat, Semporna, Tungku, Bahagian Tawau (Timur)",
    "sbh04": "SBH04 - Bandar Tawau, Balong, Merotai, Kalabakan, Bahagian Tawau (Barat)",
    "sbh05": "SBH05 - Kudat, Kota Marudu, Pitas, Pulau Banggi, Bahagian Kudat",
    "sbh06": "SBH06 - Gunung Kinabalu",
    "sbh07": "SBH07 - Kota Kinabalu, Ranau, Kota Belud, Tuaran, Penampang, Papar, Putatan, Bahagian Pantai Barat",
    "sbh08": "SBH08 - Pensiangan, Keningau, Tambunan, Nabawan, Bahagian Pendalaman (Atas)",
    "sbh09": "SBH09 - Beaufort, Kuala Penyu, Sipitang, Tenom, Long Pasia, Membakut, Weston, Bahagian Pendalaman (Bawah)",
    "sgr01": "SGR01 - Gombak, Petaling, Sepang, Hulu Langat, Hulu Selangor, S.Alam",
    "sgr02": "SGR02 - Kuala Selangor, Sabak Bernam",
    "sgr03": "SGR03 - Klang, Kuala Langat",
    "swk01": "SWK01 - Limbang, Lawas, Sundar, Trusan",
    "swk02": "SWK02 - Miri, Niah, Bekenu, Sibuti, Marudi",
    "swk03": "SWK03 - Pandan, Belaga, Suai, Tatau, Sebauh, Bintulu",
    "swk04": "SWK04 - Sibu, Mukah, Dalat, Song, Igan, Oya, Balingian, Kanowit, Kapit",
    "swk05": "SWK05 - Sarikei, Matu, Julau, Rajang, Daro, Bintangor, Belawai",
    "swk06": "SWK06 - Lubok Antu, Sri Aman, Roban, Debak, Kabong, Lingga, Engkelili, Betong, Spaoh, Pusa, Saratok",
    "swk07": "SWK07 - Serian, Simunjan, Samarahan, Sebuyau, Meludam",
    "swk08": "SWK08 - Kuching, Bau, Lundu, Sematan",
    "swk09": "SWK09 - Zon Khas (Kampung Patarikan)",
    "trg01": "TRG01 - Kuala Terengganu, Marang, Kuala Nerus",
    "trg02": "TRG02 - Besut, Setiu",
    "trg03": "TRG03 - Hulu Terengganu",
    "trg04": "TRG04 - Dungun, Kemaman",
    "wly01": "WLY01 - Kuala Lumpur, Putrajaya",
    "wly02": "WLY02 - Labuan"
}
