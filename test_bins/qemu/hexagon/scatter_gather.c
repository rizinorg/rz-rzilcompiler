/* scatter the 16 bit elements using C */
void scalar_scatter_16(unsigned short *vscatter16)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter16[half_offsets[i] / 2] = half_values[i];
    }
}

void check_scatter_16()
{
    memset(vscatter16_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16(vscatter16_ref);
    check_buffer(__func__, vtcm.vscatter16, vscatter16_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* scatter the 16 bit elements using C */
void scalar_scatter_16_acc(unsigned short *vscatter16)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter16[half_offsets[i] / 2] += half_values_acc[i];
    }
}

/* scatter-accumulate the 16 bit elements using C */
void check_scatter_16_acc()
{
    memset(vscatter16_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16(vscatter16_ref);
    scalar_scatter_16_acc(vscatter16_ref);
    check_buffer(__func__, vtcm.vscatter16, vscatter16_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* masked scatter the 16 bit elements using C */
void scalar_scatter_16_masked(unsigned short *vscatter16)
{
    for (int i = 0; i < MATRIX_SIZE; i++) {
        if (half_predicates[i]) {
            vscatter16[half_offsets[i] / 2] = half_values_masked[i];
        }
    }

}

void check_scatter_16_masked()
{
    memset(vscatter16_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16(vscatter16_ref);
    scalar_scatter_16_acc(vscatter16_ref);
    scalar_scatter_16_masked(vscatter16_ref);
    check_buffer(__func__, vtcm.vscatter16, vscatter16_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* scatter the 32 bit elements using C */
void scalar_scatter_32(unsigned int *vscatter32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter32[word_offsets[i] / 4] = word_values[i];
    }
}

void check_scatter_32()
{
    memset(vscatter32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned int));
    scalar_scatter_32(vscatter32_ref);
    check_buffer(__func__, vtcm.vscatter32, vscatter32_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned int));
}

/* scatter-accumulate the 32 bit elements using C */
void scalar_scatter_32_acc(unsigned int *vscatter32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter32[word_offsets[i] / 4] += word_values_acc[i];
    }
}

void check_scatter_32_acc()
{
    memset(vscatter32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned int));
    scalar_scatter_32(vscatter32_ref);
    scalar_scatter_32_acc(vscatter32_ref);
    check_buffer(__func__, vtcm.vscatter32, vscatter32_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned int));
}

/* masked scatter the 32 bit elements using C */
void scalar_scatter_32_masked(unsigned int *vscatter32)
{
    for (int i = 0; i < MATRIX_SIZE; i++) {
        if (word_predicates[i]) {
            vscatter32[word_offsets[i] / 4] = word_values_masked[i];
        }
    }
}

void check_scatter_32_masked()
{
    memset(vscatter32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned int));
    scalar_scatter_32(vscatter32_ref);
    scalar_scatter_32_acc(vscatter32_ref);
    scalar_scatter_32_masked(vscatter32_ref);
    check_buffer(__func__, vtcm.vscatter32, vscatter32_ref,
                  SCATTER_BUFFER_SIZE * sizeof(unsigned int));
}

/* scatter the 16 bit elements with 32 bit offsets using C */
void scalar_scatter_16_32(unsigned short *vscatter16_32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter16_32[word_offsets[i] / 2] = half_values[i];
    }
}

void check_scatter_16_32()
{
    memset(vscatter16_32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16_32(vscatter16_32_ref);
    check_buffer(__func__, vtcm.vscatter16_32, vscatter16_32_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* scatter-accumulate the 16 bit elements with 32 bit offsets using C */
void scalar_scatter_16_32_acc(unsigned short *vscatter16_32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vscatter16_32[word_offsets[i] / 2] += half_values_acc[i];
    }
}

void check_scatter_16_32_acc()
{
    memset(vscatter16_32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16_32(vscatter16_32_ref);
    scalar_scatter_16_32_acc(vscatter16_32_ref);
    check_buffer(__func__, vtcm.vscatter16_32, vscatter16_32_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* masked scatter the 16 bit elements with 32 bit offsets using C */
void scalar_scatter_16_32_masked(unsigned short *vscatter16_32)
{
    for (int i = 0; i < MATRIX_SIZE; i++) {
        if (half_predicates[i]) {
            vscatter16_32[word_offsets[i] / 2] = half_values_masked[i];
        }
    }
}

void check_scatter_16_32_masked()
{
    memset(vscatter16_32_ref, FILL_CHAR,
           SCATTER_BUFFER_SIZE * sizeof(unsigned short));
    scalar_scatter_16_32(vscatter16_32_ref);
    scalar_scatter_16_32_acc(vscatter16_32_ref);
    scalar_scatter_16_32_masked(vscatter16_32_ref);
    check_buffer(__func__, vtcm.vscatter16_32, vscatter16_32_ref,
                 SCATTER_BUFFER_SIZE * sizeof(unsigned short));
}

/* gather the elements from the scatter buffer using C */
void scalar_gather_16(unsigned short *vgather16)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vgather16[i] = vtcm.vscatter16[half_offsets[i] / 2];
    }
}

void check_gather_16()
{
      memset(vgather16_ref, 0, MATRIX_SIZE * sizeof(unsigned short));
      scalar_gather_16(vgather16_ref);
      check_buffer(__func__, vtcm.vgather16, vgather16_ref,
                   MATRIX_SIZE * sizeof(unsigned short));
}

/* masked gather the elements from the scatter buffer using C */
void scalar_gather_16_masked(unsigned short *vgather16)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        if (half_predicates[i]) {
            vgather16[i] = vtcm.vscatter16[half_offsets[i] / 2];
        }
    }
}

void check_gather_16_masked()
{
    memset(vgather16_ref, gather_16_masked_init(),
           MATRIX_SIZE * sizeof(unsigned short));
    scalar_gather_16_masked(vgather16_ref);
    check_buffer(__func__, vtcm.vgather16, vgather16_ref,
                 MATRIX_SIZE * sizeof(unsigned short));
}

/* gather the elements from the scatter32 buffer using C */
void scalar_gather_32(unsigned int *vgather32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vgather32[i] = vtcm.vscatter32[word_offsets[i] / 4];
    }
}

void check_gather_32(void)
{
    memset(vgather32_ref, 0, MATRIX_SIZE * sizeof(unsigned int));
    scalar_gather_32(vgather32_ref);
    check_buffer(__func__, vtcm.vgather32, vgather32_ref,
                 MATRIX_SIZE * sizeof(unsigned int));
}

/* masked gather the elements from the scatter32 buffer using C */
void scalar_gather_32_masked(unsigned int *vgather32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        if (word_predicates[i]) {
            vgather32[i] = vtcm.vscatter32[word_offsets[i] / 4];
        }
    }
}

void check_gather_32_masked(void)
{
    memset(vgather32_ref, gather_32_masked_init(),
           MATRIX_SIZE * sizeof(unsigned int));
    scalar_gather_32_masked(vgather32_ref);
    check_buffer(__func__, vtcm.vgather32,
                 vgather32_ref, MATRIX_SIZE * sizeof(unsigned int));
}

/* gather the elements from the scatter16_32 buffer using C */
void scalar_gather_16_32(unsigned short *vgather16_32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        vgather16_32[i] = vtcm.vscatter16_32[word_offsets[i] / 2];
    }
}

void check_gather_16_32(void)
{
    memset(vgather16_32_ref, 0, MATRIX_SIZE * sizeof(unsigned short));
    scalar_gather_16_32(vgather16_32_ref);
    check_buffer(__func__, vtcm.vgather16_32, vgather16_32_ref,
                 MATRIX_SIZE * sizeof(unsigned short));
}

/* masked gather the elements from the scatter16_32 buffer using C */
void scalar_gather_16_32_masked(unsigned short *vgather16_32)
{
    for (int i = 0; i < MATRIX_SIZE; ++i) {
        if (half_predicates[i]) {
            vgather16_32[i] = vtcm.vscatter16_32[word_offsets[i] / 2];
        }
    }

}

void check_gather_16_32_masked(void)
{
    memset(vgather16_32_ref, gather_16_masked_init(),
           MATRIX_SIZE * sizeof(unsigned short));
    scalar_gather_16_32_masked(vgather16_32_ref);
    check_buffer(__func__, vtcm.vgather16_32, vgather16_32_ref,
                 MATRIX_SIZE * sizeof(unsigned short));
}

/* print scatter16 buffer */
void print_scatter16_buffer(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 16 bit scatter buffer");

        for (int i = 0; i < SCATTER_BUFFER_SIZE; i++) {
            if ((i % MATRIX_SIZE) == 0) {
                printf("\n");
            }
            for (int j = 0; j < 2; j++) {
                printf("%c", (char)((vtcm.vscatter16[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

/* print the gather 16 buffer */
void print_gather_result_16(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 16 bit gather result\n");

        for (int i = 0; i < MATRIX_SIZE; i++) {
            for (int j = 0; j < 2; j++) {
                printf("%c", (char)((vtcm.vgather16[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

/* print the scatter32 buffer */
void print_scatter32_buffer(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 32 bit scatter buffer");

        for (int i = 0; i < SCATTER_BUFFER_SIZE; i++) {
            if ((i % MATRIX_SIZE) == 0) {
                printf("\n");
            }
            for (int j = 0; j < 4; j++) {
                printf("%c", (char)((vtcm.vscatter32[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

/* print the gather 32 buffer */
void print_gather_result_32(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 32 bit gather result\n");

        for (int i = 0; i < MATRIX_SIZE; i++) {
            for (int j = 0; j < 4; j++) {
                printf("%c", (char)((vtcm.vgather32[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

/* print the scatter16_32 buffer */
void print_scatter16_32_buffer(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 16_32 bit scatter buffer");

        for (int i = 0; i < SCATTER_BUFFER_SIZE; i++) {
            if ((i % MATRIX_SIZE) == 0) {
                printf("\n");
            }
            for (int j = 0; j < 2; j++) {
                printf("%c",
                      (unsigned char)((vtcm.vscatter16_32[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

/* print the gather 16_32 buffer */
void print_gather_result_16_32(void)
{
    if (PRINT_DATA) {
        printf("\n\nPrinting the 16_32 bit gather result\n");

        for (int i = 0; i < MATRIX_SIZE; i++) {
            for (int j = 0; j < 2; j++) {
                printf("%c",
                       (unsigned char)((vtcm.vgather16_32[i] >> j * 8) & 0xff));
            }
            printf(" ");
        }
        printf("\n");
    }
}

int main()
{
    prefill_vtcm_scratch();

    /* 16 bit elements with 16 bit offsets */
    create_offsets_values_preds_16();

    vector_scatter_16();
    print_scatter16_buffer();
    check_scatter_16();

    vector_gather_16();
    print_gather_result_16();
    check_gather_16();

    vector_gather_16_masked();
    print_gather_result_16();
    check_gather_16_masked();

    vector_scatter_16_acc();
    print_scatter16_buffer();
    check_scatter_16_acc();

    vector_scatter_16_masked();
    print_scatter16_buffer();
    check_scatter_16_masked();

    /* 32 bit elements with 32 bit offsets */
    create_offsets_values_preds_32();

    vector_scatter_32();
    print_scatter32_buffer();
    check_scatter_32();

    vector_gather_32();
    print_gather_result_32();
    check_gather_32();

    vector_gather_32_masked();
    print_gather_result_32();
    check_gather_32_masked();

    vector_scatter_32_acc();
    print_scatter32_buffer();
    check_scatter_32_acc();

    vector_scatter_32_masked();
    print_scatter32_buffer();
    check_scatter_32_masked();

    /* 16 bit elements with 32 bit offsets */
    create_offsets_values_preds_16_32();

    vector_scatter_16_32();
    print_scatter16_32_buffer();
    check_scatter_16_32();

    vector_gather_16_32();
    print_gather_result_16_32();
    check_gather_16_32();

    vector_gather_16_32_masked();
    print_gather_result_16_32();
    check_gather_16_32_masked();

    vector_scatter_16_32_acc();
    print_scatter16_32_buffer();
    check_scatter_16_32_acc();

    vector_scatter_16_32_masked();
    print_scatter16_32_buffer();
    check_scatter_16_32_masked();

    puts(err ? "FAIL" : "PASS");
    return err;
}
