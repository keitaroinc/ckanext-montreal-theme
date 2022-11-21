"use strict";

// Include gulp.
const gulp = require("gulp");
const config = require("./config.json");

// Include plugins.
const sass_compiler = require("sass");
const sass = require("gulp-sass")(sass_compiler);
const plumber = require("gulp-plumber");
const glob = require("gulp-sass-glob");
const uglify = require("gulp-uglify");
const concat = require("gulp-concat");
const notify = require("gulp-notify");
const rename = require("gulp-rename");
const sourcemaps = require("gulp-sourcemaps");
const postcss = require("gulp-postcss");
const autoprefixer = require("autoprefixer");
const tailwindcss = require('tailwindcss');
const postcssPresetEnv = require('postcss-preset-env');
const del = require("del");

// Process CSS for production.
gulp.task("css", function () {
  var postcssPlugins = [require('postcss-import'),
                        postcssPresetEnv({
                          features: {
                            'nesting-rules': true
                          }}),
                        autoprefixer("last 2 versions", "> 1%", "ie 10"),
                        tailwindcss('tailwind.config.js')];

  return gulp
    .src(config.css.src)
    .pipe(glob())
    .pipe(
      plumber({
        errorHandler: function (error) {
          notify.onError({
            title: "Gulp",
            subtitle: "Failure!",
            message: "Error: <%= error.message %>",
          })(error);
          this.emit("end");
        },
      })
    )
    .pipe(
      sass({
        outputStyle: "compressed",
        errLogToConsole: true,
      })
    )
    .pipe(postcss(postcssPlugins))
    .pipe(gulp.dest(config.css.dest));
});

// Process CSS for development.
gulp.task("css_dev", function () {
  var postcssPlugins = [require('postcss-import'),
                        postcssPresetEnv({
                          features: {
                            'nesting-rules': true
                          }}),
                        autoprefixer("last 2 versions", "> 1%", "ie 10"),
                        tailwindcss('tailwind.config.js')];

  return gulp
    .src(config.css.src)
    .pipe(glob())
    .pipe(
      plumber({
        errorHandler: function (error) {
          notify.onError({
            title: "Gulp",
            subtitle: "Failure!",
            message: "Error: <%= error.message %>",
          })(error);
          this.emit("end");
        },
      })
    )
    .pipe(sourcemaps.init())
    .pipe(
      sass({
        outputStyle: "compact",
        errLogToConsole: true,
      })
    )
    .pipe(postcss(postcssPlugins))
    .pipe(sourcemaps.write("./"))
    .pipe(gulp.dest(config.css.dest));
});

// // Compress images.
// gulp.task('images', function () {
//   return gulp.src(config.images.src)
//       .pipe(imagemin([
//         imagemin.gifsicle({interlaced: true}),
//         imagemin.mozjpeg({progressive: true}),
//         imagemin.optipng({optimizationLevel: 5}),
//         imagemin.svgo({
//           plugins: [
//             {removeViewBox: false},
//             {cleanupIDs: false}
//           ]
//         })
//       ]))
//       .pipe(gulp.dest(config.images.dest));
// });

// Concat all JS files into one file and minify it.
gulp.task("scripts", function () {
  return gulp
    .src(config.js.src)
    .pipe(
      plumber({
        errorHandler: function (error) {
          notify.onError({
            title: "Gulp scripts processing",
            subtitle: "Failure!",
            message: "Error: <%= error.message %>",
          })(error);
          this.emit("end");
        },
      })
    )
    .pipe(concat("./index.js"))
    .pipe(gulp.dest("./assets/scripts/"))
    .pipe(rename(config.js.file))
    .pipe(uglify())
    .pipe(gulp.dest(config.js.dest));
});

// Concat all JS files into one file.
gulp.task("scripts_dev", function () {
  return gulp
    .src(config.js.src)
    .pipe(
      plumber({
        errorHandler: function (error) {
          notify.onError({
            title: "Gulp scripts processing",
            subtitle: "Failure!",
            message: "Error: <%= error.message %>",
          })(error);
          this.emit("end");
        },
      })
    )
    .pipe(concat("./index.js"))
    .pipe(gulp.dest("./assets/scripts/"))
    .pipe(sourcemaps.init())
    .pipe(rename(config.js.file))
    .pipe(sourcemaps.write("./"))
    .pipe(gulp.dest(config.js.dest))
    .pipe(
      notify({
        message: "Rebuild all custom scripts. Please refresh your browser",
        onLast: true,
      })
    );
});

// Remove temporary JS storage.
gulp.task("removeTemporaryStorage", function () {
  return del("./assets/scripts/");
});

// Remove sourcemaps.
gulp.task("removeSourceMaps", function () {
  return del(["./css/style.css.map", "./css/ckeditor-style.css.map"]);
});

// Watch task.
gulp.task("watch", function () {
  gulp.watch(config.css.src, { usePolling: true }, gulp.series("css_dev"));
  gulp.watch(
    config.js.src,
    { usePolling: true },
    gulp.series("scripts_dev", "removeTemporaryStorage")
  );
});

// Compile for production.
gulp.task(
  "serve",
  gulp.parallel(
    "css",
    gulp.series("scripts", "removeTemporaryStorage"),
    "removeSourceMaps"
  )
);

// Compile for development + Watch
gulp.task(
  "serve_dev",
  gulp.series(
    gulp.parallel(
      "css_dev",
      gulp.series("scripts_dev", "removeTemporaryStorage")
    )
  )
);

// Default Task
gulp.task("default", gulp.series("serve"));

// Development Task
gulp.task("dev", gulp.series("serve_dev"));
