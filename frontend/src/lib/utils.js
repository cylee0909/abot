import pinyin from 'pinyin'

// 获取字符串的拼音首字母
export const getPinyinFirstLetters = (text) => {
  const pinyinArray = pinyin(text, {
    style: pinyin.STYLE_NORMAL,
    segment: false
  })
  return pinyinArray.map(item => item[0][0]).join('').toLowerCase()
}

// 获取字符串的完整拼音
export const getPinyin = (text) => {
  const pinyinArray = pinyin(text, {
    style: pinyin.STYLE_NORMAL,
    segment: false
  })
  return pinyinArray.map(item => item[0]).join('').toLowerCase()
}
