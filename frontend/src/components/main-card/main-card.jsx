import React from "react";
import { Link } from "react-router-dom";

import defaultImg from "../../images/default-kitty.jpg";
import { URL } from "../../utils/constants";

import styles from "./main-card.module.css";

export const MainCard = ({
  cardId,
  name = "",
  date = "",
  color = "Бежевый",
  img,
  extraClass = "",
}) => {
  const colorText =
    color === "black" ||
    color === "saddlebrown" ||
    color === "gray" ||
    color === "darkgray"
      ? "white"
      : "primary";

  // Функция для формирования правильного URL изображения
  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return defaultImg;
    
    // Если URL уже начинается с http, проверяем нужно ли добавить порт
    if (imageUrl.startsWith('http')) {
      // Заменяем http://localhost на http://localhost:9000
      if (imageUrl.startsWith('http://localhost/')) {
        return imageUrl.replace('http://localhost/', 'http://localhost:9000/');
      }
      return imageUrl;
    }
    
    // Иначе добавляем базовый URL
    return `${URL}${imageUrl.startsWith('/') ? '' : '/'}${imageUrl}`;
  };

  return (
    <article className={`${styles.content} ${extraClass}`}>
      <Link className={styles.link} to={`/cats/${cardId}`}>
        <img
          className={styles.img}
          src={getImageUrl(img)}
          alt="Фото котика."
        />
      </Link>
      <div className={styles.data_box}>
        <div className={styles.name_n_date_box}>
          <p
            className={`text text_type_h3 text_color_primary mt-8 mb-3 ${styles.name}`}
          >
            {name}
          </p>
          <p
            className={`text text_type_medium-20 text_color_secondary mb-8 ${styles.date}`}
          >
            {date}
          </p>
        </div>
        <div
          className={styles.cat_color_box}
          style={{ backgroundColor: color }}
        >
          <p
            className={`text text_type_medium-20 text_color_${colorText} ${styles.cat_color}`}
          >
            {color}
          </p>
        </div>
      </div>
    </article>
  );
};
