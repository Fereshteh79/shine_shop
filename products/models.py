from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify

ZERO = Decimal("0.00")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی",
    )

    class Meta:
        abstract = True


def generate_unique_slug(
        model,
        *,
        text: str,
        slug_field: str = "slug",
        pk: int | None = None,
) -> str:
    """
    تولید slug یکتا با پشتیبانی از زبان فارسی.

    اگر slug پایه قبلاً وجود داشته باشد:
        product
        product-2
        product-3
        ...
    """

    base = slugify(text, allow_unicode=True) or "item"

    queryset = model.objects.all()

    if pk is not None:
        queryset = queryset.exclude(pk=pk)

    slug = base
    counter = 2

    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1

    return slug


class Category(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="نام دسته‌بندی",
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True,
        verbose_name="تصویر",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ("name",)
        indexes = [
            models.Index(
                fields=("is_active", "slug"),
                name="category_active_slug_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Category,
                text=self.name,
                pk=self.pk,
            )

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "shop:category",
            kwargs={"slug": self.slug},
        )


class Brand(models.Model):
    name = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="نام برند",
    )
    slug = models.SlugField(
        max_length=140,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    logo = models.ImageField(
        upload_to="brands/",
        blank=True,
        null=True,
        verbose_name="لوگو",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ("name",)
        indexes = [
            models.Index(
                fields=("is_active", "slug"),
                name="brand_active_slug_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Brand,
                text=self.name,
                pk=self.pk,
            )

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "shop:brand",
            kwargs={"slug": self.slug},
        )


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="دسته‌بندی",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="برند",
    )

    name = models.CharField(
        max_length=255,
        verbose_name="نام محصول",
    )
    slug = models.SlugField(
        max_length=280,
        unique=True,
        allow_unicode=True,
        verbose_name="اسلاگ",
    )
    sku = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="کد محصول",
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="توضیح کوتاه",
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
    )

    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(ZERO),
        ],
        verbose_name="قیمت",
    )
    discount_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(ZERO),
        ],
        verbose_name="قیمت تخفیف",
    )

    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی",
    )

    is_available = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="قابل فروش",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="محصول ویژه",
    )

    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان SEO",
    )
    meta_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="توضیحات SEO",
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("is_available", "category"),
                name="product_available_category_idx",
            ),
            models.Index(
                fields=("is_available", "brand"),
                name="product_available_brand_idx",
            ),
            models.Index(
                fields=("is_featured", "is_available"),
                name="product_featured_available_idx",
            ),
            models.Index(
                fields=("-created_at",),
                name="product_created_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def final_price(self) -> Decimal:
        if (
                self.discount_price is not None
                and self.discount_price < self.price
        ):
            return self.discount_price

        return self.price

    @property
    def has_discount(self) -> bool:
        return (
                self.discount_price is not None
                and self.discount_price < self.price
        )

    @property
    def discount_percentage(self) -> int:
        if not self.has_discount or self.price <= ZERO:
            return 0

        percentage = (
                (self.price - self.final_price)
                * Decimal("100")
                / self.price
        )

        return round(percentage)

    @property
    def in_stock(self) -> bool:
        return (
                self.is_available
                and self.stock > 0
        )

    @property
    def primary_image(self):
        """
        تصویر اصلی محصول.

        در حالت عادی constraint دیتابیس تضمین می‌کند
        فقط یک تصویر primary باشد.
        """
        images = getattr(self, "_prefetched_objects_cache", {}).get("images")

        if images is not None:
            return next(
                (
                    image
                    for image in images
                    if image.is_primary
                ),
                images[0] if images else None,
            )

        return (
                self.images
                .filter(is_primary=True)
                .first()
                or self.images.first()
        )

    @property
    def seo_title(self) -> str:
        return self.meta_title.strip() or self.name

    @property
    def seo_description(self) -> str:
        return (
                self.meta_description.strip()
                or self.short_description.strip()
                or self.description[:160].strip()
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(
                Product,
                text=self.name,
                pk=self.pk,
            )

        if (
                self.discount_price is not None
                and self.discount_price >= self.price
        ):
            self.discount_price = None

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "products:detail",
            kwargs={"slug": self.slug},
        )


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="محصول",
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/",
        verbose_name="تصویر",
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="متن جایگزین",
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name="تصویر اصلی",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب",
    )

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصولات"
        ordering = ("sort_order", "id")

        indexes = [
            models.Index(
                fields=("product", "sort_order"),
                name="product_image_order_idx",
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=("product",),
                condition=Q(is_primary=True),
                name="unique_primary_image_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - تصویر {self.pk}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = self.product.name

        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True,
            ).exclude(
                pk=self.pk,
            ).update(
                is_primary=False,
            )

        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="محصول",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="نام تنوع",
    )
    sku = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="کد تنوع",
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(ZERO),
        ],
        verbose_name="قیمت",
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال",
    )

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌های محصول"
        ordering = ("id",)

        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_variant_name_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}"

    @property
    def final_price(self) -> Decimal:
        if self.price is not None:
            return self.price

        return self.product.final_price

    @property
    def in_stock(self) -> bool:
        return (
                self.is_active
                and self.product.is_available
                and self.stock > 0
        )


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attributes",
        verbose_name="محصول",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="ویژگی",
    )
    value = models.CharField(
        max_length=255,
        verbose_name="مقدار",
    )

    class Meta:
        verbose_name = "ویژگی محصول"
        verbose_name_plural = "ویژگی‌های محصولات"
        ordering = ("id",)

        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_attribute_name_per_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"
